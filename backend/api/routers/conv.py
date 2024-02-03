import uuid
from typing import List, Union

import httpx
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, and_, delete

from api.database.sqlalchemy import get_async_session_context
from api.enums import ChatSourceTypes
from api.exceptions import InvalidParamsException, AuthorityDenyException, InternalException, OpenaiWebException
from api.models.db import User, OpenaiWebConversation, BaseConversation
from api.models.doc import OpenaiApiConversationHistoryDocument, OpenaiWebConversationHistoryDocument, \
    BaseConversationHistory
from api.response import response
from api.schemas import OpenaiWebConversationSchema, BaseConversationSchema, OpenaiApiConversationSchema
from api.schemas.openai_schemas import OpenaiChatInterpreterInfo
from api.sources import OpenaiWebChatManager
from api.users import current_active_user, current_super_user
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
openai_web_manager = OpenaiWebChatManager()


async def _get_conversation_by_id(conversation_id: str | uuid.UUID, user: User = Depends(current_active_user)):
    async with get_async_session_context() as session:
        r = await session.execute(
            select(BaseConversation).where(BaseConversation.conversation_id == str(conversation_id)))
        conversation = r.scalars().one_or_none()
        if conversation is None:
            raise InvalidParamsException("errors.conversationNotFound")
        if not user.is_superuser and conversation.user_id != user.id:
            raise AuthorityDenyException
        return conversation


@router.get("/conv", tags=["conversation"],
            response_model=List[
                BaseConversationSchema | OpenaiWebConversationSchema | OpenaiApiConversationSchema])
async def get_my_conversations(user: User = Depends(current_active_user)):
    """
    返回自己的有效会话
    """
    async with get_async_session_context() as session:
        r = await session.execute(select(BaseConversation).where(
            and_(BaseConversation.user_id == user.id, BaseConversation.is_valid == True)
        ))
        results = r.scalars().all()
        results = jsonable_encoder(results)
        return results


@router.get("/conv/all", tags=["conversation"],
            response_model=List[BaseConversationSchema])
async def get_all_conversations(_user: User = Depends(current_super_user), valid_only: bool = False):
    async with get_async_session_context() as session:
        stat = True
        if valid_only:
            stat = BaseConversation.is_valid == True
        r = await session.execute(select(BaseConversation).where(stat))
        results = r.scalars().all()
        results = jsonable_encoder(results)
        return results


@router.get("/conv/{conversation_id}", tags=["conversation"],
            response_model=OpenaiApiConversationHistoryDocument | OpenaiWebConversationHistoryDocument | BaseConversationHistory)
async def get_conversation_history(conversation: BaseConversation = Depends(_get_conversation_by_id),
                                   user: User = Depends(current_active_user)):
    if conversation.source == ChatSourceTypes.openai_web:
        try:
            result = await openai_web_manager.get_conversation_history(conversation.conversation_id,
                                                                       conversation.source_id)
            if result.current_model != conversation.current_model or not conversation.is_valid:
                async with get_async_session_context() as session:
                    conversation = await session.get(BaseConversation, conversation.id)
                    conversation.current_model = result.current_model
                    conversation.is_valid = True
                    await session.commit()
            return result
        except httpx.TimeoutException as e:
            logger.warning(
                f"{conversation.conversation_id} get conversation history timeout: {e.__class__.__name__}")
            raise InternalException("errors.timeout")
        except OpenaiWebException as e:
            if e.code == 404:
                if conversation.is_valid:
                    async with get_async_session_context() as session:
                        conversation = await session.get(BaseConversation, conversation.id)
                        conversation.is_valid = False
                        await session.commit()
            raise e
        except Exception as e:
            logger.warning(
                f"{conversation.conversation_id} get conversation history failed: {e.__class__.__name__} {e}")
            raise e
    else:
        doc = await OpenaiApiConversationHistoryDocument.get(conversation.conversation_id)
        if doc is None:
            raise InvalidParamsException("errors.conversationNotFound")
        return doc


@router.get("/conv/{conversation_id}/cache", tags=["conversation"],
            response_model=OpenaiApiConversationHistoryDocument | OpenaiWebConversationHistoryDocument | BaseConversationHistory)
async def get_conversation_history_from_cache(conversation_id, user: User = Depends(current_super_user)):
    conversation = await _get_conversation_by_id(conversation_id, user=user)
    if conversation.source == ChatSourceTypes.openai_web:
        doc = await OpenaiWebConversationHistoryDocument.get(conversation.conversation_id)
    else:
        doc = await OpenaiApiConversationHistoryDocument.get(conversation.conversation_id)
    if doc is None:
        raise InvalidParamsException("errors.conversationNotFound")
    return doc


@router.delete("/conv/{conversation_id}", tags=["conversation"])
async def delete_conversation(conversation: BaseConversation = Depends(_get_conversation_by_id),
                              user: User = Depends(current_active_user)):
    """
    软删除：标记为 invalid 并且从 chatgpt 账号中删除会话，但不会删除 mongodb 中的历史记录
    """
    if not conversation.is_valid:
        raise InvalidParamsException("errors.conversationAlreadyDeleted")
    if conversation.source == ChatSourceTypes.openai_web:
        try:
            await openai_web_manager.delete_conversation(conversation.conversation_id, conversation.source_id)
        except OpenaiWebException as e:
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
async def vanish_conversation(conversation: BaseConversation = Depends(_get_conversation_by_id),
                              _user: User = Depends(current_super_user)):
    """
    硬删除：删除数据库和账号中的对话和历史记录
    """
    if conversation.is_valid:
        await delete_conversation(conversation, conversation.source_id)
    if conversation.source == ChatSourceTypes.openai_web:
        doc = await OpenaiWebConversationHistoryDocument.get(conversation.conversation_id)
    else:  # api
        doc = await OpenaiApiConversationHistoryDocument.get(conversation.conversation_id)
    if doc is not None:
        await doc.delete()
    async with get_async_session_context() as session:
        await session.execute(
            delete(BaseConversation).where(BaseConversation.conversation_id == conversation.conversation_id))
        await session.commit()
    return response(200)


@router.patch("/conv/{conversation_id}", tags=["conversation"], response_model=BaseConversationSchema)
async def update_conversation_title(title: str, conversation: BaseConversation = Depends(_get_conversation_by_id),
                                    user: User = Depends(current_active_user)):
    if conversation.source == ChatSourceTypes.openai_web:
        await openai_web_manager.set_conversation_title(conversation.conversation_id,
                                                        title, conversation.source_id)
    else:  # api
        doc = await OpenaiApiConversationHistoryDocument.get(conversation.conversation_id)
        if doc is None:
            raise InvalidParamsException("errors.conversationNotFound")
        doc.title = title
        await doc.save()
    async with get_async_session_context() as session:
        conversation.title = title
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
    result = jsonable_encoder(conversation)
    return result


@router.patch("/conv/{conversation_id}/assign/{username}", tags=["conversation"])
async def assign_conversation(username: str, conversation: BaseConversation = Depends(_get_conversation_by_id),
                              _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        user = await session.execute(select(User).where(User.username == username))
        user = user.scalars().one_or_none()
        if user is None:
            raise InvalidParamsException("errors.userNotFound")
        conversation.user_id = user.id
        session.add(conversation)
        await session.commit()
    return response(200)


@router.delete("/conv", tags=["conversation"])
async def delete_all_conversation(_user: User = Depends(current_super_user)):
    await openai_web_manager.clear_conversations()
    await openai_web_manager.clear_conversations(use_team=True)
    async with get_async_session_context() as session:
        await session.execute(delete(OpenaiWebConversation))
        await session.commit()
    return response(200)


@router.patch("/conv/{conversation_id}/gen_title", tags=["conversation"], response_model=str)
async def generate_conversation_title(message_id: str,
                                      conversation: OpenaiWebConversation = Depends(_get_conversation_by_id),
                                      _user: User = Depends(current_active_user)):
    async with get_async_session_context() as session:
        title = await openai_web_manager.generate_conversation_title(conversation.conversation_id, message_id,
                                                                     conversation.source_id)
        if title:
            conversation.title = title
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
        else:
            raise InternalException("errors.generateTitleFailed")
        return title


@router.get("/conv/{conversation_id}/interpreter", tags=["conversation"], response_model=OpenaiChatInterpreterInfo)
async def get_conversation_interpreter_info(conversation: OpenaiWebConversation = Depends(_get_conversation_by_id),
                                            _user: User = Depends(current_active_user)):
    url = await openai_web_manager.get_interpreter_info(conversation.conversation_id, conversation.source_id)
    return response(200, result=url)


@router.get("/conv/{conversation_id}/interpreter/download-url", tags=["conversation"])
async def get_conversation_interpreter_download_url(message_id: str, sandbox_path: str,
                                                    conversation: OpenaiWebConversation = Depends(
                                                        _get_conversation_by_id),
                                                    _user: User = Depends(current_active_user)):
    if message_id is None or sandbox_path is None:
        raise InvalidParamsException("message_id and sandbox_path are required")
    url = await openai_web_manager.get_interpreter_file_download_url(conversation.conversation_id, message_id,
                                                                     sandbox_path,
                                                                     conversation.source_id)
    return response(200, result=url)
