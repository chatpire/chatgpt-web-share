import asyncio
import json
import time
from datetime import datetime
from typing import List

import httpx
import requests
from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder
from httpx import HTTPError
from sqlalchemy import select, or_, and_, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.requests import Request

import api.chatgpt
import api.globals as g
import api.globals as g

config = g.config
from api.database import get_async_session_context
from api.enums import ChatStatus, ChatModels
from api.exceptions import InvalidParamsException, AuthorityDenyException
from api.models import User, Conversation
from api.schema import ConversationSchema, AskParams, AskResponse
from api.users import current_active_user, websocket_auth, current_super_user
from revChatGPT.typings import Error as revChatGPTError
from api.response import response
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


async def get_conversation_by_uuid(conversation_id: str, session: AsyncSession):
    r = await session.execute(select(Conversation).where(Conversation.conversation_id == conversation_id))
    conversation = r.scalars().one_or_none()
    return conversation


async def get_conversation_by_uuid_depend(conversation_id: str, user: User = Depends(current_active_user)):
    async with get_async_session_context() as session:
        conversation = await get_conversation_by_uuid(conversation_id, session)
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
async def get_conversation_history(conversation: Conversation = Depends(get_conversation_by_uuid_depend)):
    result = await api.chatgpt.chatgpt_manager.get_conversation_messages(conversation.conversation_id)
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
async def delete_conversation(conversation: Conversation = Depends(get_conversation_by_uuid_depend)):
    """remove conversation from database and chatgpt server"""
    if not conversation.is_valid:
        raise InvalidParamsException("errors.conversationAlreadyDeleted")
    try:
        await api.chatgpt.chatgpt_manager.delete_conversation(conversation.conversation_id)
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
async def vanish_conversation(conversation: Conversation = Depends(get_conversation_by_uuid_depend)):
    # try:
    #     await g.chatgpt_manager.delete_conversation(conversation.conversation_id)
    # except revChatGPTError as e:
    #     logger.warning(f"delete conversation {conversation.conversation_id} failed: {e.code} {e.message}")
    # except httpx.HTTPStatusError as e:
    #     if e.response.status_code != 404:
    #         raise e
    if conversation.is_valid:
        try:
            await api.chatgpt.chatgpt_manager.delete_conversation(conversation.conversation_id)
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
async def change_conversation_title(title: str, conversation: Conversation = Depends(get_conversation_by_uuid_depend)):
    await api.chatgpt.chatgpt_manager.set_conversation_title(conversation.conversation_id,
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
        conversation = get_conversation_by_uuid(conversation_id, session)
        if conversation is None:
            raise InvalidParamsException("errors.conversationNotFound")
        conversation.user_id = user.id
        session.add(conversation)
        await session.commit()
    return response(200)


@router.patch("/conv/{conversation_id}/gen_title", tags=["conversation"], response_model=ConversationSchema)
async def generate_conversation_title(message_id: str,
                                      conversation: Conversation = Depends(get_conversation_by_uuid_depend)):
    if conversation.title is not None:
        raise InvalidParamsException("errors.conversationTitleAlreadyGenerated")
    async with get_async_session_context() as session:
        result = await api.chatgpt.chatgpt_manager.generate_conversation_title(conversation.id, message_id)
        if result["title"]:
            conversation.title = result["title"]
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
        else:
            raise InvalidParamsException(f"{result['message']}")
    result = jsonable_encoder(conversation)
    return result


async def change_user_chat_status(user_id: int, status: ChatStatus):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        user.chat_status = status
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@router.post("/conv", tags=["conversation"], response_model=AskResponse)
async def ask(askParams: AskParams, user: User = Depends(current_active_user)):
    start_time = time.time()

    if user.chat_status != ChatStatus.idling:
        raise api.exceptions.InvalidRequestException("errors.cannotConnectMoreThanOneClient")

    if askParams.parent_id is not None and askParams.conversation_id is None:
        raise api.exceptions.InvalidParamsException("errors.missingConversationId")

    is_new_conv = askParams.conversation_id is None
    if not is_new_conv:
        conversation = await get_conversation_by_uuid_depend(askParams.conversation_id, user)
        if conversation is None:
            raise api.exceptions.InvalidParamsException("errors.conversationNotFound")
        model_name = askParams.model_name or conversation.model_name
    else:
        model_name = askParams.model_name or ChatModels.default

    if isinstance(model_name, str):
        model_name = ChatModels(model_name)
    if model_name == ChatModels.paid and not user.can_use_paid:
        raise api.exceptions.InvalidParamsException("errors.userNotAllowToUsePaidModel")
    if model_name == ChatModels.gpt4 and not user.can_use_gpt4:
        raise api.exceptions.InvalidParamsException("errors.userNotAllowToUseGPT4Model")
    if model_name in [ChatModels.gpt4, ChatModels.paid] and not config.get("chatgpt_paid", False):
        raise api.exceptions.InvalidParamsException("errors.paidModelNotAvailable")

    # 判断是否能新建对话，以及是否能继续提问
    async with get_async_session_context() as session:
        user_conversations_count = await session.execute(
            select(func.count(Conversation.id)).filter(and_(Conversation.user_id == user.id, Conversation.is_valid)))
        user_conversations_count = user_conversations_count.scalar()
        if is_new_conv and user.max_conv_count != -1 and user_conversations_count >= user.max_conv_count:
            raise api.exceptions.InvalidParamsException("errors.maxConversationCountReached")
        if user.available_ask_count != -1 and user.available_ask_count <= 0:
            raise api.exceptions.InvalidParamsException("errors.noAvailableAskCount")
        if user.available_gpt4_ask_count != -1 and user.available_gpt4_ask_count <= 0 and model_name == ChatModels.gpt4:
            raise api.exceptions.InvalidParamsException("errors.noAvailableGPT4AskCount")

    message = askParams.message
    parent_id = askParams.parent_id
    timeout = askParams.timeout
    new_title = askParams.new_title
    conversation_id = askParams.conversation_id

    logger.debug(f"User {user.username} start asking, model: {model_name}")

    is_success = False
    is_aborted = False
    is_queueing = False
    has_got_reply = False
    queueing_start_time = None
    ask_start_time = None

    event = asyncio.Event()

    def ask_response(askResponse: AskResponse):
        return json.dumps((jsonable_encoder(askResponse))) + "\n"

    async def post_process():
        nonlocal user, conversation_id, new_title, is_new_conv
        nonlocal is_success, is_aborted, has_got_reply

        user = await change_user_chat_status(user.id, ChatStatus.idling)

        try:
            if is_success or (is_aborted and has_got_reply):
                async with get_async_session_context() as ses:
                    # 若新建了对话，则添加到数据库
                    if is_new_conv and conversation_id is not None:
                        # 设置默认标题
                        try:
                            if askParams.new_title is not None:
                                await api.chatgpt.chatgpt_manager.set_conversation_title(conversation_id,
                                                                                         askParams.new_title)
                        except Exception as e:
                            logger.warning(e)
                        finally:
                            current_time = datetime.utcnow()
                            conv = Conversation(conversation_id=conversation_id, title=new_title,
                                                user_id=user.id,
                                                model_name=model_name, create_time=current_time,
                                                active_time=current_time)
                            ses.add(conv)
                    # 更新 conversation
                    if not is_new_conv:
                        conv = await get_conversation_by_uuid(conversation_id,
                                                              ses)  # 此前的 conversation 属于另一个session
                        conv.active_time = datetime.utcnow()
                        if conv.model_name != model_name:
                            conv.model_name = model_name
                        ses.add(conv)
                    # 扣除一次对话次数
                    # 这里的逻辑是：available_ask_count 是总的对话次数，available_gpt4_ask_count 是 GPT4 的对话次数
                    # 如果都有限制，则都要扣除一次. TODO: 改成分开计数
                    # 如果 available_ask_count 不限但是 available_gpt4_ask_count 限制，则只扣除 available_gpt4_ask_count
                    if user.available_ask_count != -1 or user.available_gpt4_ask_count != -1:
                        user = await ses.get(User, user.id)
                        if user.available_ask_count != -1:
                            assert user.available_ask_count > 0
                            user.available_ask_count -= 1
                        if model_name == ChatModels.gpt4 and user.available_gpt4_ask_count != -1:
                            assert user.available_gpt4_ask_count > 0
                            user.available_gpt4_ask_count -= 1
                        ses.add(user)
                    await ses.commit()
        except Exception as e:
            logger.error(str(e))
            raise e
            # if not is_aborted:
            #     yield ask_response(AskResponse(
            #         type="error",
            #         tip="errors.unknownError",
            #         message=str(e)
            #     ))

    async def streamer():
        nonlocal user, conversation_id, parent_id, message, timeout, model_name, new_title, is_new_conv
        nonlocal queueing_start_time, ask_start_time
        nonlocal is_success, is_aborted, has_got_reply, is_queueing

        try:
            queueing_start_time = time.time()

            if api.chatgpt.chatgpt_manager.is_busy():
                is_queueing = True
                yield ask_response(AskResponse(type="waiting", tip="tips.queueing"))  # 通知用户正在排队

            await change_user_chat_status(user.id, ChatStatus.queueing)
            async with api.chatgpt.chatgpt_manager.semaphore:
                is_queueing = False
                await change_user_chat_status(user.id, ChatStatus.asking)
                yield ask_response(AskResponse(type="waiting", tip="tips.waiting"))  # 通知用户正在等待回复
                ask_start_time = time.time()
                try:
                    async for data in api.chatgpt.chatgpt_manager.ask(message, conversation_id, parent_id, timeout,
                                                                      model_name):
                        if conversation_id is None:
                            conversation_id = data["conversation_id"]
                        if not has_got_reply:
                            print("got reply")
                        has_got_reply = True
                        yield ask_response(AskResponse(
                            type="message",
                            message=data["message"],
                            conversation_id=data["conversation_id"],
                            parent_id=data["parent_id"],
                            model_name=data["model"],
                        ))
                    is_success = True
                except requests.exceptions.Timeout as e:
                    yield ask_response(AskResponse(
                        type="error",
                        tip="errors.chatgptResponseError",
                        message=f"{e.source} {e.code}: {e.message}"
                    ))
                except revChatGPTError as e:
                    yield ask_response(AskResponse(
                        type="error",
                        tip="errors.chatgptResponseError",
                        message=f"{e.source} {e.code}: {e.message}"
                    ))
                except HTTPError as e:
                    logger.error(str(e))
                    yield ask_response(AskResponse(
                        type="error",
                        tip="errors.httpError",
                        message=str(e)
                    ))
                except Exception as e:
                    # 修复 message 为 None 时的错误
                    if str(e).startswith("Field missing"):
                        logger.warning(str(e))
                    else:
                        logger.error(str(e))
                        yield ask_response(AskResponse(
                            type="error",
                            tip="errors.unknownError",
                            message=str(e)
                        ))
        except asyncio.CancelledError:
            is_aborted = True
        finally:
            stop_time = time.time()
            queueing_duration = stop_time - queueing_start_time
            if ask_start_time is not None:
                ask_duration = stop_time - ask_start_time
            else:
                ask_duration = None

            if is_success:
                logger.debug(
                    f"finished ask {conversation_id} ({model_name}). "
                    f"ask: {ask_duration:.2f}s, queueing: {queueing_duration:.2f}s")
            elif is_aborted:
                if is_queueing:
                    logger.info(f"ask {conversation_id} ({model_name}) cancelled by user while queueing. "
                                f"queueing: {queueing_duration:.2f}s")
                elif not has_got_reply:
                    logger.info(f"ask {conversation_id} ({model_name}) cancelled by user while waiting for reply. "
                                f"ask: {ask_duration:.2f}s, queueing: {queueing_duration:.2f}s")
                else:
                    logger.info(f"ask {conversation_id} ({model_name}) cancelled by user. "
                                f"ask: {ask_duration:.2f}s, queueing: {queueing_duration:.2f}s")
            else:
                logger.debug(
                    f"finished ask {conversation_id} ({model_name}), but reply failed. "
                    f"ask: {ask_duration:.2f}s, queueing: {queueing_duration:.2f}s")

            # 写入到 scope 中，供统计
            g.ask_log_queue.enqueue(
                (user.id, model_name.value, stop_time - ask_start_time, stop_time - start_time))
            api.chatgpt.chatgpt_manager.reset_chat()

            if not is_aborted:
                await post_process()
            else:
                asyncio.create_task(post_process())

    return StreamingResponse(streamer(), media_type="application/x-ndjson")
