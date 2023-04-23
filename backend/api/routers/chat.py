import time
from datetime import datetime

import requests
from fastapi import APIRouter
from httpx import HTTPError
from revChatGPT.typings import Error as revChatGPTError
from sqlalchemy import select, func, and_
from starlette.websockets import WebSocket
from websockets.exceptions import ConnectionClosed

import api.revchatgpt
from api import globals as g
from api.conf import Config
from api.database import get_async_session_context
from api.enums import RevChatStatus, ChatModels
from api.models import RevConversation, User
from api.routers.conv import _get_conversation_by_id
from api.users import websocket_auth
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


async def change_user_chat_status(user_id: int, status: RevChatStatus):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        user.chat_status = status
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@router.websocket("/chat")
async def ask(websocket: WebSocket):
    """
    利用 WebSocket 实时更新 ChatGPT 回复.

    客户端第一次连接：发送 { message, conversation_id?, parent_id?, use_paid?, timeout? }
        conversation_id 为空则新建会话，否则回复 parent_id 指定的消息
    服务端返回格式：{ type, tip, message, conversation_id, parent_id, use_paid, title }
    其中：type 可以为 "waiting" / "message" / "title"
    """

    await websocket.accept()
    user = await websocket_auth(websocket)
    logger.debug(f"{user.username} connected to websocket")
    websocket.scope["auth_user"] = user

    if user is None:
        await websocket.close(1008, "errors.unauthorized")
        return

    if user.chat_status != RevChatStatus.idling:
        await websocket.close(1008, "errors.cannotConnectMoreThanOneClient")
        return

    # 读取用户输入
    params = await websocket.receive_json()
    message = params.get("message", None)
    conversation_id = params.get("conversation_id", None)
    parent_id = params.get("parent_id", None)
    model_name = params.get("model_name")
    # timeout = params.get("timeout", 30)  # default 30s
    timeout = Config().get_config().chatgpt.ask_timeout
    new_title = params.get("new_title", None)

    if message is None:
        await websocket.close(1007, "errors.missingMessage")
        return
    if parent_id is not None and conversation_id is None:
        await websocket.close(1007, "errors.missingConversationId")
        return

    is_new_conv = conversation_id is None
    conversation = None
    if not is_new_conv:
        conversation = await _get_conversation_by_id(conversation_id, user)
        model_name = model_name or conversation.model_name
    else:
        model_name = model_name or ChatModels.default

    if isinstance(model_name, str):
        model_name = ChatModels(model_name)
    if model_name == ChatModels.paid and not user.can_use_paid:
        await websocket.close(1007, "errors.userNotAllowToUsePaidModel")
        return
    if model_name == ChatModels.gpt4 and not user.can_use_gpt4:
        await websocket.close(1007, "errors.userNotAllowToUseGPT4Model")
        return
    if model_name in [ChatModels.gpt4, ChatModels.paid] and not Config().get_config().chatgpt.is_plus_account:
        await websocket.close(1007, "errors.paidModelNotAvailable")
        return

    # 判断是否能新建对话，以及是否能继续提问
    async with get_async_session_context() as session:
        user_conversations_count = await session.execute(
            select(func.count(RevConversation.id)).filter(and_(RevConversation.user_id == user.id, RevConversation.is_valid)))
        user_conversations_count = user_conversations_count.scalar()
        if is_new_conv and user.max_conv_count != -1 and user_conversations_count >= user.max_conv_count:
            await websocket.close(1008, "errors.maxConversationCountReached")
            return
        if user.available_ask_count != -1 and user.available_ask_count <= 0:
            await websocket.close(1008, "errors.noAvailableAskCount")
            return
        if user.available_gpt4_ask_count != -1 and user.available_gpt4_ask_count <= 0 and model_name == ChatModels.gpt4:
            await websocket.close(1008, "errors.noAvailableGPT4AskCount")
            return

    if api.revchatgpt.chatgpt_manager.is_busy():
        await websocket.send_json({
            "type": "queueing",
            "tip": "tips.queueing"
        })

    websocket_code = 1001
    websocket_reason = "tips.terminated"

    is_completed = False
    is_canceled = False
    has_got_reply = False
    ask_start_time = None
    queueing_start_time = None

    def check_message(msg: str):
        url = Config().get_config().chatgpt.chatgpt_base_url
        if url and url in msg:
            return msg.replace(url, "<chatgpt_base_url>")

    try:
        # 标记用户为 queueing
        await change_user_chat_status(user.id, RevChatStatus.queueing)
        # is_queueing = True
        queueing_start_time = time.time()
        async with api.revchatgpt.chatgpt_manager.semaphore:
            is_queueing = False
            try:
                await change_user_chat_status(user.id, RevChatStatus.asking)
                await websocket.send_json({
                    "type": "waiting",
                    "tip": "tips.waiting"
                })
                ask_start_time = time.time()
                api.revchatgpt.chatgpt_manager.reset_chat()
                async for data in api.revchatgpt.chatgpt_manager.ask(message, conversation_id, parent_id, timeout,
                                                                     model_name):
                    has_got_reply = True
                    reply = {
                        "type": "message",
                        "message": data["message"],
                        "conversation_id": data["conversation_id"],
                        "parent_id": data["parent_id"],
                        "model_name": data["model"],
                    }
                    await websocket.send_json(reply)
                    if conversation_id is None:
                        conversation_id = data["conversation_id"]
                is_completed = True
            except Exception as e:
                # 修复 message 为 None 时的错误
                if str(e).startswith("Field missing"):
                    logger.warning(str(e))
                else:
                    raise e
            finally:
                api.revchatgpt.chatgpt_manager.reset_chat()

    except ConnectionClosed:
        # print("websocket aborted", e.code)
        is_canceled = True
    except requests.exceptions.Timeout:
        logger.warning(str(e))
        await websocket.send_json({
            "type": "error",
            "tip": "errors.timeout"
        })
        websocket_code = 1001
        websocket_reason = "errors.timout"
    except revChatGPTError as e:
        logger.error(str(e))
        message = check_message(f"{e.source} {e.code}: {e.message}")
        await websocket.send_json({
            "type": "error",
            "tip": "errors.chatgptResponseError",
            "message": message
        })
        websocket_code = 1001
        websocket_reason = "errors.chatgptResponseError"
    except HTTPError as e:
        logger.error(str(e))
        message = check_message(str(e))
        await websocket.send_json({
            "type": "error",
            "tip": "errors.httpError",
            "message": message
        })
        websocket_code = 1014
        websocket_reason = "errors.httpError"
    except Exception as e:
        logger.error(str(e))
        message = check_message(str(e))
        await websocket.send_json({
            "type": "error",
            "tip": "errors.unknownError",
            "message": message
        })
        websocket_code = 1011
        websocket_reason = "errors.unknownError"

    ask_stop_time = time.time()

    queueing_time = ask_stop_time - queueing_start_time
    queueing_time = round(queueing_time, 3)
    if ask_start_time is not None:
        ask_time = ask_stop_time - ask_start_time
        ask_time = round(ask_time, 3)
    else:
        ask_time = None

    if is_completed:
        logger.debug(
            f"finished ask {conversation_id} ({model_name}), user: {user.id}, "
            f"ask: {ask_time}s, total: {queueing_time}s")
        websocket_code = 1000
        websocket_reason = "tips.finished"
    elif is_canceled:
        if has_got_reply:
            logger.debug(
                f"canceled ask {conversation_id} ({model_name}) while replying, user: {user.id}, "
                f"ask: {ask_time}s, total: {queueing_time}s")
        elif is_queueing:
            logger.debug(
                f"canceled ask {conversation_id} ({model_name}) while queueing, user: {user.id}, "
                f"total: {queueing_time}s")
        else:
            logger.debug(
                f"canceled ask {conversation_id} ({model_name}) before replying, user: {user.id}, "
                f"total: {queueing_time}s")
    else:
        logger.debug(
            f"terminated ask {conversation_id} ({model_name}) because of error")

    try:
        if has_got_reply:
            async with get_async_session_context() as session:
                # 若新建了对话，则添加到数据库
                if is_new_conv and conversation_id is not None:
                    # 设置默认标题
                    try:
                        if new_title is not None:
                            await api.revchatgpt.chatgpt_manager.set_conversation_title(conversation_id, new_title)
                    except Exception as e:
                        logger.warning(e)
                    finally:
                        current_time = datetime.utcnow()
                        conversation = RevConversation(conversation_id=conversation_id, title=new_title,
                                                       user_id=user.id,
                                                       model_name=model_name, create_time=current_time,
                                                       active_time=current_time)
                        session.add(conversation)
                # 更新 conversation
                if not is_new_conv:
                    conversation = await session.get(RevConversation, conversation.id)  # 此前的 conversation 属于另一个session
                    conversation.active_time = datetime.utcnow()
                    if conversation.model_name != model_name:
                        conversation.model_name = model_name
                    session.add(conversation)

                # 扣除一次对话次数
                # 这里的逻辑是：available_ask_count 是总的对话次数，available_gpt4_ask_count 是 GPT4 的对话次数
                # 如果都有限制，则都要扣除一次
                # 如果 available_ask_count 不限但是 available_gpt4_ask_count 限制，则只扣除 available_gpt4_ask_count
                if user.available_ask_count != -1 or user.available_gpt4_ask_count != -1:
                    user = await session.get(User, user.id)
                    if user.available_ask_count != -1:
                        assert user.available_ask_count > 0
                        user.available_ask_count -= 1
                    if model_name == ChatModels.gpt4 and user.available_gpt4_ask_count != -1:
                        assert user.available_gpt4_ask_count > 0
                        user.available_gpt4_ask_count -= 1
                    session.add(user)
                await session.commit()

                # 写入到 scope 中，供统计
                g.ask_log_queue.enqueue(
                    (user.id, model_name.value, ask_time, queueing_time))
    except Exception as e:
        raise e
    finally:
        await change_user_chat_status(user.id, RevChatStatus.idling)
        await websocket.close(websocket_code, websocket_reason)
