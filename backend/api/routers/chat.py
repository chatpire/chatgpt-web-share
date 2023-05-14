import time
from datetime import datetime

import requests
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from httpx import HTTPError
from pydantic import ValidationError
from revChatGPT.typings import Error as revChatGPTError
from sqlalchemy import select, func, and_
from starlette.websockets import WebSocket
from websockets.exceptions import ConnectionClosed

from api import globals as g
from api.conf import Config
from api.database import get_async_session_context
from api.enums import RevChatStatus, ChatSourceTypes
from api.exceptions import InternalException
from api.models.db import RevConversation, User
from api.routers.conv import _get_conversation_by_id
from api.schema import RevConversationSchema, AskRequest, AskResponse, AskResponseType, UserReadAdmin
from api.sources import RevChatGPTManager, convert_revchatgpt_message
from api.users import websocket_auth
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
manager = RevChatGPTManager()


async def change_user_chat_status(user_id: int, status: RevChatStatus):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        user.rev_chat_status = status
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


# @router.get("/chat/avaliable-models", tags=["chat"])
# async def get_avaliable_models(_user: User = Depends(current_active_user)):
#     return [model.value for model in RevChatModels]

@router.get("/chat/__schema_types", tags=["chat"], response_model=AskResponse)
async def _predict_schema_types(_request: AskRequest):
    """
    只用来让 openapi 自动生成 schema，并不实际调用
    """
    raise InternalException()


@router.websocket("/chat")
async def chat(websocket: WebSocket):
    """
    利用 WebSocket 实时更新 ChatGPT 回复
    """

    async def reply(response: AskResponse):
        await websocket.send_json(jsonable_encoder(response))

    await websocket.accept()
    user_db = await websocket_auth(websocket)
    if user_db is None:
        await websocket.close(1008, "errors.unauthorized")
        return

    logger.debug(f"{user_db.username} connected to websocket")
    websocket.scope["auth_user"] = user_db

    user = UserReadAdmin.from_orm(user_db)

    if user.rev_chat_status != RevChatStatus.idling:
        await websocket.close(1008, "errors.cannotConnectMoreThanOneClient")
        return

    # 读取用户输入
    params = await websocket.receive_json()
    timeout = Config().revchatgpt.ask_timeout  # TODO: 完善超时机制
    try:
        ask_request = AskRequest(**params)
    except ValidationError as e:
        await reply(AskResponse(type=AskResponseType.error, error_detail=str(e)))
        await websocket.close(1007, "errors.invalidAskRequest")
        return

    # 是否允许使用当前提问类型
    if ask_request.type == ChatSourceTypes.rev and not user.setting.can_use_revchatgpt \
            or ask_request.type == ChatSourceTypes.api and not user.setting.can_use_openai_api:
        await websocket.close(1007, "errors.userNotAllowToUseChatType")
        return

    conversation = None
    conversation_id = None
    if not ask_request.new_conversation:
        assert ask_request.conversation_id is not None
        conversation_id = ask_request.conversation_id
        conversation = await _get_conversation_by_id(ask_request.conversation_id, user_db)

    # 判断是否能使用该模型
    if ask_request.type == ChatSourceTypes.rev and ask_request.model not in user.setting.revchatgpt_available_models or \
            ask_request.type == ChatSourceTypes.api and ask_request.model not in user.setting.openai_api_available_models:
        await websocket.close(1007, "errors.userNotAllowToUseModel")
        return

    # 判断是否能新建对话，以及是否能继续提问
    if ask_request.type == ChatSourceTypes.rev:
        async with get_async_session_context() as session:
            rev_conv_count = await session.execute(
                select(func.count(RevConversation.id)).filter(
                    and_(RevConversation.user_id == user.id, RevConversation.is_valid)))
            rev_conv_count = rev_conv_count.scalar()

            # user_setting = UserSettingSchema.from_orm(user.setting)
            max_conv_count = user.setting.revchatgpt_ask_limits.max_conv_count
            model_ask_count = user.setting.revchatgpt_ask_limits.per_model_ask_count.get(ask_request.model, -1)
            total_ask_count = user.setting.revchatgpt_ask_limits.total_ask_count
            if ask_request.new_conversation and max_conv_count != -1 and rev_conv_count >= max_conv_count:
                await websocket.close(1008, "errors.maxConversationCountReached")
                return
            if total_ask_count != -1 and total_ask_count <= 0:
                await websocket.close(1008, "errors.noAvailableTotalAskCount")
                return
            if model_ask_count != -1 and model_ask_count <= 0:
                await websocket.close(1008, "errors.noAvailableModelAskCount")
                return

    if manager.is_busy():
        await reply(AskResponse(
            type=AskResponseType.queueing,
            tip="tips.queueing"
        ))

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
        async with manager.semaphore:
            is_queueing = False
            try:
                await change_user_chat_status(user.id, RevChatStatus.asking)
                await reply(AskResponse(
                    type=AskResponseType.waiting,
                    tip="tips.waiting"
                ))
                ask_start_time = time.time()
                manager.reset_chat()
                async for data in manager.ask(content=ask_request.content, conversation_id=ask_request.conversation_id,
                                              parent_id=ask_request.parent,
                                              timeout=timeout,
                                              model=ask_request.model):
                    has_got_reply = True
                    message = convert_revchatgpt_message(data)
                    if conversation_id is None:
                        conversation_id = data.get("conversation_id", None)
                    await reply(AskResponse(
                        type=AskResponseType.message,
                        conversation_id=conversation_id,
                        message=message
                    ))
                is_completed = True
            except Exception as e:
                # 修复 message 为 None 时的错误
                if str(e).startswith("Field missing"):
                    logger.warning(str(e))
                else:
                    raise e
            finally:
                manager.reset_chat()

    except ConnectionClosed:
        # print("websocket aborted", e.code)
        is_canceled = True
    except requests.exceptions.Timeout:
        logger.warning(str(e))
        await reply(AskResponse(
            type=AskResponseType.error,
            tip="errors.timout"
        ))
        websocket_code = 1001
        websocket_reason = "errors.timout"
    except revChatGPTError as e:
        logger.error(str(e))
        content = check_message(f"{e.source} {e.code}: {e.message}")
        # await websocket.send_json({
        #     "type": "error",
        #     "tip": "errors.chatgptResponseError",
        #     "message": content
        # })
        await reply(AskResponse(
            type=AskResponseType.error,
            tip="errors.chatgptResponseError",
            error_detail=content
        ))
        websocket_code = 1001
        websocket_reason = "errors.chatgptResponseError"
    except HTTPError as e:
        logger.error(str(e))
        content = check_message(str(e))
        # await websocket.send_json({
        #     "type": "error",
        #     "tip": "errors.httpError",
        #     "message": content
        # })
        await reply(AskResponse(
            type=AskResponseType.error,
            tip="errors.httpError",
            error_detail=content
        ))
        websocket_code = 1014
        websocket_reason = "errors.httpError"
    except Exception as e:
        logger.error(str(e))
        content = check_message(str(e))
        # await websocket.send_json({
        #     "type": "error",
        #     "tip": "errors.unknownError",
        #     "message": content
        # })
        await reply(AskResponse(
            type=AskResponseType.error,
            tip="errors.unknownError",
            error_detail=content
        ))
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
            f"finished ask {conversation_id} ({ask_request.model}), user: {user.id}, "
            f"ask: {ask_time}s, total: {queueing_time}s")
        websocket_code = 1000
        websocket_reason = "tips.finished"
    elif is_canceled:
        if has_got_reply:
            logger.debug(
                f"canceled ask {conversation_id} ({ask_request.model}) while replying, user: {user.id}, "
                f"ask: {ask_time}s, total: {queueing_time}s")
        elif is_queueing:
            logger.debug(
                f"canceled ask {conversation_id} ({ask_request.model}) while queueing, user: {user.id}, "
                f"total: {queueing_time}s")
        else:
            logger.debug(
                f"canceled ask {conversation_id} ({ask_request.model}) before replying, user: {user.id}, "
                f"total: {queueing_time}s")
    else:
        logger.debug(
            f"terminated ask {conversation_id} ({ask_request.model}) because of error")

    try:
        if has_got_reply:
            async with get_async_session_context() as session:
                # 若新建了对话，则添加到数据库
                if ask_request.new_conversation and conversation_id is not None:
                    # 设置默认标题
                    try:
                        if ask_request.new_title is not None:
                            await manager.set_conversation_title(str(conversation_id), ask_request.new_title)
                    except Exception as e:
                        logger.warning(e)
                    finally:
                        current_time = datetime.utcnow()
                        rev_conversation = RevConversationSchema(
                            conversation_id=conversation_id, title=ask_request.new_title, user_id=user.id,
                            current_model=ask_request.model, create_time=current_time, update_time=current_time
                        )
                        conversation = RevConversation(**rev_conversation.dict())
                        session.add(conversation)
                # 更新 conversation
                if not ask_request.new_conversation:
                    conversation = await session.get(RevConversation, conversation.id)  # 此前的 conversation 属于另一个session
                    conversation.update_time = datetime.utcnow()
                    if conversation.current_model != ask_request.model:
                        conversation.current_model = ask_request.model
                    session.add(conversation)

                # 扣除对话次数
                # total_ask_count = user.setting.revchatgpt_ask_limits.total_count
                # model_ask_count = user.setting.revchatgpt_ask_limits.per_model_count.get(model_name.value, -1)
                if total_ask_count != -1 or model_ask_count != -1:
                    user = await session.get(User, user.id)
                    if total_ask_count != -1:
                        assert total_ask_count > 0
                        user.setting.revchatgpt_ask_limits.total_ask_count -= 1
                    if model_ask_count != -1:
                        assert model_ask_count > 0
                        user.setting.revchatgpt_ask_limits.per_model_ask_count[ask_request.model] -= 1
                    session.add(user.setting)
                await session.commit()

                # 写入到 scope 中，供统计
                g.ask_log_queue.enqueue(
                    (user.id, ask_request.model.value, ask_time, queueing_time))
    except Exception as e:
        raise e
    finally:
        await change_user_chat_status(user.id, RevChatStatus.idling)
        await websocket.close(websocket_code, websocket_reason)
