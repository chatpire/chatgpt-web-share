import time
from datetime import datetime

import requests
from fastapi import APIRouter, Depends
from httpx import HTTPError
from revChatGPT.typings import Error as revChatGPTError
from sqlalchemy import select, func, and_
from starlette.websockets import WebSocket
from websockets.exceptions import ConnectionClosed
from api import globals as g
from api.conf import Config
from api.database import get_async_session_context
from api.enums import RevChatStatus, ChatModel
from api.models import RevConversation, User
from api.routers.conv import _get_conversation_by_id
from api.schema import RevConversationSchema
from api.users import websocket_auth, current_active_user
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


async def change_user_chat_status(user_id: int, status: RevChatStatus):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        user.rev_chat_status = status
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@router.get("/chat/avaliable-models", tags=["chat"])
async def get_avaliable_models(_user: User = Depends(current_active_user)):
    # TODO 允许设置全局可用模型
    return [model.value for model in RevChatModels]


@router.websocket("/chat")
async def ask_revchatgpt(websocket: WebSocket):
    """
    利用 WebSocket 实时更新 ChatGPT 回复.

    客户端第一次连接：发送 { message, conversation_id?, parent_id?, use_paid?, timeout? }
        conversation_id 为空则新建会话，否则回复 parent_id 指定的消息
    服务端返回格式：{ type, tip, message, conversation_id, parent_id, use_paid, title }
    其中：type 可以为 "waiting" / "message" / "title"
    """

    await websocket.accept()
    user = await websocket_auth(websocket)
    if user is None:
        await websocket.close(1008, "errors.unauthorized")
        return

    logger.debug(f"{user.username} connected to websocket")
    websocket.scope["auth_user"] = user

    if user.rev_chat_status != RevChatStatus.idling:
        await websocket.close(1008, "errors.cannotConnectMoreThanOneClient")
        return

    # 读取用户输入
    params = await websocket.receive_json()
    message = params.get("message", None)
    conversation_id = params.get("conversation_id", None)
    parent_id = params.get("parent_id", None)
    model_name = params.get("model_name")
    timeout = Config().revchatgpt.ask_timeout
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
        model_name = model_name or ChatModel.gpt_3_5

    if isinstance(model_name, str):
        model_name = ChatModel(model_name)

    # 判断是否能使用该模型
    if model_name.value not in user.setting.revchatgpt_available_models:
        await websocket.close(1007, "errors.userNotAllowToUseModel")
        return

    # 判断是否能新建对话，以及是否能继续提问
    async with get_async_session_context() as session:
        user_conversations_count = await session.execute(
            select(func.count(RevConversation.id)).filter(
                and_(RevConversation.user_id == user.id, RevConversation.is_valid)))
        user_conversations_count = user_conversations_count.scalar()

        # user_setting = UserSettingSchema.from_orm(user.setting)
        max_conv_count = user.setting.revchatgpt_ask_limits.max_conv_count
        model_ask_count = user.setting.revchatgpt_ask_limits.per_model_count.get(model_name.value, -1)
        total_ask_count = user.setting.revchatgpt_ask_limits.total_count
        if is_new_conv and max_conv_count != -1 and user_conversations_count >= max_conv_count:
            await websocket.close(1008, "errors.maxConversationCountReached")
            return
        if total_ask_count != -1 and total_ask_count <= 0:
            await websocket.close(1008, "errors.noAvailableTotalAskCount")
            return
        if model_ask_count != -1 and model_ask_count <= 0:
            await websocket.close(1008, "errors.noAvailableModelAskCount")
            return

    if g.chatgpt_manager.is_busy():
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
        url = Config().revchatgpt.chatgpt_base_url
        if url and url in msg:
            return msg.replace(url, "<chatgpt_base_url>")

    try:
        # 标记用户为 queueing
        await change_user_chat_status(user.id, RevChatStatus.queueing)
        queueing_start_time = time.time()
        async with g.chatgpt_manager.semaphore:
            is_queueing = False
            try:
                await change_user_chat_status(user.id, RevChatStatus.asking)
                await websocket.send_json({
                    "type": "waiting",
                    "tip": "tips.waiting"
                })
                ask_start_time = time.time()
                g.chatgpt_manager.reset_chat()
                async for data in g.chatgpt_manager.ask(message, conversation_id, parent_id,
                                                        timeout,
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
                g.chatgpt_manager.reset_chat()

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
                            await g.chatgpt_manager.set_conversation_title(conversation_id, new_title)
                    except Exception as e:
                        logger.warning(e)
                    finally:
                        current_time = datetime.utcnow()
                        rev_conversation = RevConversationSchema(
                            conversation_id=conversation_id, title=new_title, user_id=user.id,
                            model_name=model_name, create_time=current_time, update_time=current_time
                        )
                        conversation = RevConversation(**rev_conversation.dict())
                        session.add(conversation)
                # 更新 conversation
                if not is_new_conv:
                    conversation = await session.get(RevConversation, conversation.id)  # 此前的 conversation 属于另一个session
                    conversation.update_time = datetime.utcnow()
                    if conversation.model_name != model_name:
                        conversation.model_name = model_name
                    session.add(conversation)

                # 扣除对话次数
                # total_ask_count = user.setting.revchatgpt_ask_limits.total_count
                # model_ask_count = user.setting.revchatgpt_ask_limits.per_model_count.get(model_name.value, -1)
                if total_ask_count != -1 or model_ask_count != -1:
                    user = await session.get(User, user.id)
                    if total_ask_count != -1:
                        assert total_ask_count > 0
                        user.setting.revchatgpt_ask_limits.total_count -= 1
                    if model_ask_count != -1:
                        assert model_ask_count > 0
                        user.setting.revchatgpt_ask_limits.per_model_count[model_name.value] -= 1
                    session.add(user.setting)
                await session.commit()

                # 写入到 scope 中，供统计
                g.ask_log_queue.enqueue(
                    (user.id, model_name.value, ask_time, queueing_time))
    except Exception as e:
        raise e
    finally:
        await change_user_chat_status(user.id, RevChatStatus.idling)
        await websocket.close(websocket_code, websocket_reason)
