from typing import List

import httpx
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, and_, delete
import api.revchatgpt

from api.database import get_async_session_context
from api.enums import ChatModels
from api.exceptions import InvalidParamsException, AuthorityDenyException, InternalException
from api.models import User, RevConversation
from api.schema import RevConversationSchema
from api.users import current_active_user, current_super_user
from revChatGPT.typings import Error as revChatGPTError
from api.response import response
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


async def _get_conversation_by_id(conversation_id: str, user: User = Depends(current_active_user)):
    async with get_async_session_context() as session:
        r = await session.execute(select(RevConversation).where(RevConversation.conversation_id == conversation_id))
        conversation = r.scalars().one_or_none()
        if conversation is None:
            raise InvalidParamsException("errors.conversationNotFound")
        if not user.is_superuser and conversation.user_id != user.id:
            raise AuthorityDenyException
        return conversation


@router.get("/conv", tags=["conversation"], response_model=List[RevConversationSchema])
async def get_all_conversations(user: User = Depends(current_active_user), fetch_all: bool = False):
    """
    返回自己的有效会话
    对于管理员，返回所有对话，并可以指定是否只返回有效会话
    """
    if fetch_all and not user.is_superuser:
        raise AuthorityDenyException()

    stat = and_(RevConversation.user_id == user.id, RevConversation.is_valid)
    if fetch_all:
        stat = None
    async with get_async_session_context() as session:
        if stat is not None:
            r = await session.execute(select(RevConversation).where(stat))
        else:
            r = await session.execute(select(RevConversation))
        results = r.scalars().all()
        results = jsonable_encoder(results)
        return results


@router.get("/conv/{conversation_id}", tags=["conversation"])
async def get_conversation_history(conversation: RevConversation = Depends(_get_conversation_by_id)):
    try:
        result = await api.revchatgpt.chatgpt_manager.get_conversation_messages(conversation.conversation_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise InvalidParamsException("errors.conversationNotFound")
        raise InternalException()
    # 当不知道模型名时，顺便从对话中获取
    if conversation.model_name is None:
        model_name = result.get("model_name")
        if model_name is not None and not ChatModels.unknown.value:
            async with get_async_session_context() as session:
                conversation = await session.get(RevConversation, conversation.id)
                conversation.model_name = model_name
                session.add(conversation)
                await session.commit()
    return result


@router.delete("/conv/{conversation_id}", tags=["conversation"])
async def delete_conversation(conversation: RevConversation = Depends(_get_conversation_by_id)):
    """remove conversation from database and chatgpt server"""
    if not conversation.is_valid:
        raise InvalidParamsException("errors.conversationAlreadyDeleted")
    try:
        await api.revchatgpt.chatgpt_manager.delete_conversation(conversation.conversation_id)
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
async def vanish_conversation(conversation: RevConversation = Depends(_get_conversation_by_id)):
    # try:
    #     await g.chatgpt_manager.delete_conversation(conversation.conversation_id)
    # except revChatGPTError as e:
    #     logger.warning(f"delete conversation {conversation.conversation_id} failed: {e.code} {e.message}")
    # except httpx.HTTPStatusError as e:
    #     if e.response.status_code != 404:
    #         raise e
    if conversation.is_valid:
        try:
            await api.revchatgpt.chatgpt_manager.delete_conversation(conversation.conversation_id)
        except revChatGPTError as e:
            logger.warning(f"delete conversation {conversation.conversation_id} failed: {e.code} {e.message}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise e
    async with get_async_session_context() as session:
        await session.execute(delete(RevConversation).where(RevConversation.conversation_id == conversation.conversation_id))
        await session.commit()
    return response(200)


@router.patch("/conv/{conversation_id}", tags=["conversation"], response_model=RevConversationSchema)
async def update_conversation_title(title: str, conversation: RevConversation = Depends(_get_conversation_by_id)):
    await api.revchatgpt.chatgpt_manager.set_conversation_title(conversation.conversation_id,
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
            select(RevConversation).where(RevConversation.conversation_id == conversation_id))
        conversation = conversation.scalars().one_or_none()
        if conversation is None:
            raise InvalidParamsException("errors.conversationNotFound")
        conversation.user_id = user.id
        session.add(conversation)
        await session.commit()
    return response(200)


@router.delete("/conv", tags=["conversation"])
async def delete_all_conversation(_user: User = Depends(current_super_user)):
    await api.revchatgpt.chatgpt_manager.clear_conversations()
    async with get_async_session_context() as session:
        await session.execute(delete(RevConversation))
        await session.commit()
    return response(200)


@router.patch("/conv/{conversation_id}/gen_title", tags=["conversation"], response_model=RevConversationSchema)
async def generate_conversation_title(message_id: str, conversation: RevConversation = Depends(_get_conversation_by_id)):
    if conversation.title is not None:
        raise InvalidParamsException("errors.conversationTitleAlreadyGenerated")
    async with get_async_session_context() as session:
        result = await api.revchatgpt.chatgpt_manager.generate_conversation_title(conversation.id, message_id)
        if result["title"]:
            conversation.title = result["title"]
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
        else:
            raise InvalidParamsException(f"{result['message']}")
    result = jsonable_encoder(conversation)
    return result
