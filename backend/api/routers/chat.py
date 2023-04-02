import time
from datetime import datetime
from typing import List

import httpx
import requests
from fastapi import APIRouter, Depends, WebSocket
from fastapi.encoders import jsonable_encoder
from httpx import HTTPError
from sqlalchemy import select, or_, and_, delete, func
import api.globals as g
from api.globals import config
from api.database import get_async_session_context
from api.enums import ChatStatus, ChatModels
from api.exceptions import InvalidParamsException, AuthorityDenyException
from api.models import User, Conversation
from api.schema import ConversationSchema
from api.users import current_active_user, websocket_auth, current_super_user
from revChatGPT.typing import Error as revChatGPTError
from api.response import response
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


async def get_conversation_by_id(conversation_id: str, user: User = Depends(current_active_user)):
    async with get_async_session_context() as session:
        r = await session.execute(select(Conversation).where(Conversation.conversation_id == conversation_id))
        conversation = r.scalars().one_or_none()
        if conversation is None:
            raise InvalidParamsException("errors.conversationNotFound")
        if not user.is_superuser and conversation.user_id != user.id:
            raise AuthorityDenyException
        return conversation


@router.get("/conv", tags=["conversation"], response_model=List[ConversationSchema])
async def get_all_conversations(user: User = Depends(current_active_user), fetch_all: bool = False):
    """
    返回自己的有效会话
    对于管理员，返回所有对话，并可以指定是否只返回有效会话
    """
    if fetch_all and not user.is_superuser:
        raise AuthorityDenyException()

    stat = and_(Conversation.user_id == user.id, Conversation.is_valid)
    if fetch_all:
        stat = None
    async with get_async_session_context() as session:
        if stat is not None:
            r = await session.execute(select(Conversation).where(stat))
        else:
            r = await session.execute(select(Conversation))
        results = r.scalars().all()
        results = jsonable_encoder(results)
        return results


@router.get("/conv/{conversation_id}", tags=["conversation"])
async def get_conversation_history(conversation: Conversation = Depends(get_conversation_by_id)):
    result = await g.chatgpt_manager.get_conversation_messages(conversation.conversation_id)
    # 当不知道模型名时，顺便从对话中获取
    if conversation.model_name is None:
        model_name = result.get("model_name")
        if model_name is not None and not ChatModels.unknown.value:
            async with get_async_session_context() as session:
                conversation = await session.get(Conversation, conversation.id)
                conversation.model_name = model_name
                session.add(conversation)
                await session.commit()
    return result


@router.delete("/conv/{conversation_id}", tags=["conversation"])
async def delete_conversation(conversation: Conversation = Depends(get_conversation_by_id)):
    """remove conversation from database and chatgpt server"""
    if not conversation.is_valid:
        raise InvalidParamsException("errors.conversationAlreadyDeleted")
    try:
        await g.chatgpt_manager.delete_conversation(conversation.conversation_id)
    except revChatGPTError as e:
        logger.warning(f"delete conversation {conversation.conversation_id} failed: {e.code} {e.message}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 404:
            raise e
    async with get_async_session_context() as session:
        conversation.is_valid = False
        session.add(conversation)
        await session.commit()
    return response(200)


@router.delete("/conv/{conversation_id}/vanish", tags=["conversation"])
async def vanish_conversation(conversation: Conversation = Depends(get_conversation_by_id)):
    # try:
    #     await g.chatgpt_manager.delete_conversation(conversation.conversation_id)
    # except revChatGPTError as e:
    #     logger.warning(f"delete conversation {conversation.conversation_id} failed: {e.code} {e.message}")
    # except httpx.HTTPStatusError as e:
    #     if e.response.status_code != 404:
    #         raise e
    if conversation.is_valid:
        try:
            await g.chatgpt_manager.delete_conversation(conversation.conversation_id)
        except revChatGPTError as e:
            logger.warning(f"delete conversation {conversation.conversation_id} failed: {e.code} {e.message}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise e
    async with get_async_session_context() as session:
        await session.execute(delete(Conversation).where(Conversation.conversation_id == conversation.conversation_id))
        await session.commit()
    return response(200)


@router.patch("/conv/{conversation_id}", tags=["conversation"], response_model=ConversationSchema)
async def change_conversation_title(title: str, conversation: Conversation = Depends(get_conversation_by_id)):
    await g.chatgpt_manager.set_conversation_title(conversation.conversation_id,
                                                   title)
    async with get_async_session_context() as session:
        conversation.title = title
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
    result = jsonable_encoder(conversation)
    return result


@router.patch("/conv/{conversation_id}/assign/{username}", tags=["conversation"])
async def assign_conversation(username: str, conversation_id: str, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        user = await session.execute(select(User).where(User.username == username))
        user = user.scalars().one_or_none()
        if user is None:
            raise InvalidParamsException("errors.userNotFound")
        conversation = await session.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id))
        conversation = conversation.scalars().one_or_none()
        if conversation is None:
            raise InvalidParamsException("errors.conversationNotFound")
        conversation.user_id = user.id
        session.add(conversation)
        await session.commit()
    return response(200)


async def change_user_chat_status(user_id: int, status: ChatStatus):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        user.chat_status = status
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@router.patch("/conv/{conversation_id}/gen_title", tags=["conversation"], response_model=ConversationSchema)
async def generate_conversation_title(message_id: str, conversation: Conversation = Depends(get_conversation_by_id)):
    if conversation.title is not None:
        raise InvalidParamsException("errors.conversationTitleAlreadyGenerated")
    async with get_async_session_context() as session:
        result = await g.chatgpt_manager.generate_conversation_title(conversation.id, message_id)
        if result["title"]:
            conversation.title = result["title"]
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
        else:
            raise InvalidParamsException(f"{result['message']}")
    result = jsonable_encoder(conversation)
    return result


@router.websocket("/conv")
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

    if user.chat_status != ChatStatus.idling:
        await websocket.close(1008, "errors.cannotConnectMoreThanOneClient")
        return

    # 读取用户输入
    params = await websocket.receive_json()
    message = params.get("message", None)
    conversation_id = params.get("conversation_id", None)
    parent_id = params.get("parent_id", None)
    model_name = params.get("model_name")
    # timeout = params.get("timeout", 30)  # default 30s
    timeout = config.get("ask_timeout", 300)
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
        conversation = await get_conversation_by_id(conversation_id, user)
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
    if model_name in [ChatModels.gpt4, ChatModels.paid] and not config.get("chatgpt_paid", False):
        await websocket.close(1007, "errors.paidModelNotAvailable")
        return

    # 判断是否能新建对话，以及是否能继续提问
    async with get_async_session_context() as session:
        user_conversations_count = await session.execute(
            select(func.count(Conversation.id)).filter(and_(Conversation.user_id == user.id, Conversation.is_valid)))
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

    if g.chatgpt_manager.is_busy():
        await websocket.send_json({
            "type": "waiting",
            "tip": "tips.queueing"
        })

    websocket_code = 1001
    websocket_reason = "tips.terminated"
    try:
        # 标记用户为 queueing
        await change_user_chat_status(user.id, ChatStatus.queueing)

        async with g.chatgpt_manager.semaphore:
            await change_user_chat_status(user.id, ChatStatus.asking)
            await websocket.send_json({
                "type": "waiting",
                "tip": "tips.waiting"
            })
            request_start_time = time.time()
            try:
                async for data in g.chatgpt_manager.ask(message, conversation_id, parent_id, timeout, model_name):
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
            except Exception as e:
                # 修复 message 为 None 时的错误
                if str(e).startswith("Field missing"):
                    logger.warning(str(e))
                else:
                    logger.error(e)
                    raise e
            logger.debug(
                f"finish ask {conversation_id} ({model_name}), using time: {time.time() - request_start_time}s")

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
                        conversation = Conversation(conversation_id=conversation_id, title=new_title, user_id=user.id,
                                                    model_name=model_name, create_time=current_time,
                                                    active_time=current_time)
                        session.add(conversation)
                # 更新 conversation
                if not is_new_conv:
                    conversation = await session.get(Conversation, conversation.id)  # 此前的 conversation 属于另一个session
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
            websocket_code = 1000
            websocket_reason = "tips.finished"
    except requests.exceptions.Timeout:
        await websocket.send_json({
            "type": "error",
            "tip": "errors.timeout"
        })
        websocket_code = 1001
        websocket_reason = "errors.timout"
    except revChatGPTError as e:
        await websocket.send_json({
            "type": "error",
            "tip": "errors.chatgptResponseError",
            "message": f"{e.source} {e.code}: {e.message}"
        })
        websocket_code = 1001
        websocket_reason = "errors.chatgptResponseError"
    except HTTPError as e:
        logger.error(str(e))
        await websocket.send_json({
            "type": "error",
            "tip": "errors.httpError",
            "message": str(e)
        })
        websocket_code = 1014
        websocket_reason = "errors.httpError"
    except Exception as e:
        logger.error(str(e))
        await websocket.send_json({
            "type": "error",
            "tip": "errors.unknownError",
            "message": str(e)
        })
        websocket_code = 1011
        websocket_reason = "errors.unknownError"
    finally:
        await change_user_chat_status(user.id, ChatStatus.idling)
        g.chatgpt_manager.reset_chat()
        await websocket.close(websocket_code, websocket_reason)
