import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Any

import httpx
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi_cache.decorator import cache
from httpx import HTTPError
from pydantic import ValidationError
from sqlalchemy import select, func, and_
from starlette.websockets import WebSocket, WebSocketState
from websockets.exceptions import ConnectionClosed

from api.conf import Config
from api.database.sqlalchemy import get_async_session_context
from api.enums import OpenaiWebChatStatus, ChatSourceTypes, OpenaiWebChatModels, OpenaiApiChatModels
from api.exceptions import InternalException, InvalidParamsException, OpenaiException
from api.models.db import User, BaseConversation
from api.models.doc import OpenaiApiChatMessage, OpenaiApiConversationHistoryDocument, OpenaiApiChatMessageTextContent, \
    AskLogDocument, OpenaiWebAskLogMeta, \
    OpenaiApiAskLogMeta
from api.routers.conv import _get_conversation_by_id
from api.schemas import AskRequest, AskResponse, AskResponseType, UserReadAdmin, \
    BaseConversationSchema
from api.schemas.openai_schemas import OpenaiChatPlugin, OpenaiChatPluginUserSettings, OpenaiChatPluginListResponse
from api.sources import OpenaiWebChatManager, convert_openai_web_message, OpenaiApiChatManager
from api.users import websocket_auth, current_active_user, current_super_user
from utils.common import desensitize
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
openai_web_manager = OpenaiWebChatManager()
openai_api_manager = OpenaiApiChatManager()
config = Config()

INSTALLED_PLUGINS_CACHE_FILE_PATH = os.path.join(config.data.data_dir, "installed_plugin_manifests.json")
INSTALLED_PLUGINS_CACHE_EXPIRE = 3600 * 24

_installed_plugins: OpenaiChatPluginListResponse | None = None
_installed_plugins_map: dict[str, OpenaiChatPlugin] | None = None
_installed_plugins_last_update_time = None


def _load_installed_plugins_from_cache():
    global _installed_plugins, _installed_plugins_map, _installed_plugins_last_update_time
    if os.path.exists(INSTALLED_PLUGINS_CACHE_FILE_PATH):
        with open(INSTALLED_PLUGINS_CACHE_FILE_PATH, "r") as f:
            data = json.load(f)
            _installed_plugins = OpenaiChatPluginListResponse.model_validate(data["installed_plugins"])
            _installed_plugins_map = {plugin.id: plugin for plugin in _installed_plugins.items}
            _installed_plugins_last_update_time = data["installed_plugins_last_update_time"]


def _save_installed_plugins_to_cache(installed_plugins, installed_plugins_last_update_time):
    with open(INSTALLED_PLUGINS_CACHE_FILE_PATH, "w") as f:
        json.dump(jsonable_encoder({
            "installed_plugins": installed_plugins,
            "installed_plugins_last_update_time": installed_plugins_last_update_time
        }), f)


_load_installed_plugins_from_cache()


async def _refresh_installed_plugins():
    global _installed_plugins, _installed_plugins_map, _installed_plugins_last_update_time
    if _installed_plugins is None or time.time() - _installed_plugins_last_update_time > INSTALLED_PLUGINS_CACHE_EXPIRE:
        _installed_plugins = await openai_web_manager.get_installed_plugin_manifests()
        _installed_plugins_map = {plugin.id: plugin for plugin in _installed_plugins.items}
        _installed_plugins_last_update_time = time.time()
        _save_installed_plugins_to_cache(_installed_plugins, _installed_plugins_last_update_time)
    return _installed_plugins


@router.get("/chat/openai-plugins", tags=["chat"], response_model=OpenaiChatPluginListResponse)
@cache(expire=60 * 60 * 24)
async def get_openai_web_chat_plugins(offset: int = 0, limit: int = 0, category: str = "", search: str = "",
                                      _user: User = Depends(current_active_user)):
    plugins = await openai_web_manager.get_plugin_manifests(offset, limit, category, search)
    return plugins


@router.get("/chat/openai-plugins/installed", tags=["chat"], response_model=OpenaiChatPluginListResponse)
async def get_installed_openai_web_chat_plugins(_user: User = Depends(current_active_user)):
    plugins = await _refresh_installed_plugins()
    return plugins


@router.get("/chat/openai-plugins/installed/{plugin_id}", tags=["chat"], response_model=OpenaiChatPlugin)
async def get_installed_openai_web_plugin(plugin_id: str, _user: User = Depends(current_active_user)):
    await _refresh_installed_plugins()
    global _installed_plugins_map
    if plugin_id in _installed_plugins_map:
        return _installed_plugins_map[plugin_id]
    else:
        raise InvalidParamsException("errors.pluginNotFound")


@router.patch("/chat/openai-plugins/{plugin_id}/user-settings", tags=["chat"], response_model=OpenaiChatPlugin)
async def update_chat_plugin_user_settings(plugin_id: str, settings: OpenaiChatPluginUserSettings,
                                           _user: User = Depends(current_super_user)):
    if settings.is_authenticated is not None:
        raise InvalidParamsException("can not set is_authenticated")
    result = await openai_web_manager.change_plugin_user_settings(plugin_id, settings)
    assert isinstance(result, OpenaiChatPlugin)
    await _refresh_installed_plugins()
    return result


@router.get("/chat/__schema_types", tags=["chat"], response_model=AskResponse)
async def _predict_schema_types(_request: AskRequest):
    """
    只用来让 openapi 自动生成 schema，并不实际调用
    """
    raise InternalException()


class WebsocketException(Exception):
    def __init__(self, code: int, tip: str, error_detail: Optional[Any] = None):
        self.code = code
        self.tip = tip
        self.error_detail = error_detail


class WebsocketInvalidAskException(WebsocketException):
    def __init__(self, tip: str, error_detail: Optional[Any] = None):
        super().__init__(1008, tip, error_detail)


async def change_user_chat_status(user_id: int, status: OpenaiWebChatStatus):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        user.setting.openai_web_chat_status = status
        session.add(user.setting)
        await session.commit()
        await session.refresh(user)
    return user


async def check_limits(user: UserReadAdmin, ask_request: AskRequest):
    source_setting = user.setting.openai_web if ask_request.source == ChatSourceTypes.openai_web else user.setting.openai_api

    # 是否允许使用当前提问类型
    if not source_setting.allow_to_use:
        raise WebsocketInvalidAskException(tip="errors.userNotAllowToUseChatType")

    # 当前对话类型是否全局启用
    if ask_request.source == ChatSourceTypes.openai_web and not config.openai_web.enabled or \
            ask_request.source == ChatSourceTypes.openai_api and not config.openai_api.enabled:
        raise WebsocketInvalidAskException(tip="errors.chatTypeNotEnabled")

    # 是否到期
    current_datetime = datetime.now().astimezone(tz=timezone.utc)
    if source_setting.valid_until is not None and current_datetime > source_setting.valid_until:
        raise WebsocketInvalidAskException(tip="errors.userChatTypeExpired",
                                           error_detail=f"valid until: {source_setting.valid_until}")

    # 当前时间是否允许请求
    time_slots = source_setting.daily_available_time_slots  # list of {start_time, end_time} datetime.time
    if time_slots is not None and len(time_slots) > 0:
        now_time = datetime.now().time()  # TODO: 时区处理
        if not any(time_slot.start_time <= now_time <= time_slot.end_time for time_slot in time_slots):
            raise WebsocketInvalidAskException("errors.userNotAllowToAskAtThisTime")

    # TODO: 时间窗口频率限制

    # 判断是否能使用该模型
    if ask_request.source == ChatSourceTypes.openai_web and ask_request.model not in user.setting.openai_web.available_models or \
            ask_request.source == ChatSourceTypes.openai_api and ask_request.model not in user.setting.openai_api.available_models:
        raise WebsocketInvalidAskException("errors.userNotAllowToUseModel")

    # 模型是否全局启用
    if ask_request.source == ChatSourceTypes.openai_web and ask_request.model not in config.openai_web.enabled_models or \
            ask_request.source == ChatSourceTypes.openai_api and ask_request.model not in config.openai_api.enabled_models:
        raise WebsocketInvalidAskException("errors.modelNotEnabled")

    # 对话次数判断
    model_ask_count = source_setting.per_model_ask_count.root.get(ask_request.model, 0)
    total_ask_count = source_setting.total_ask_count
    if total_ask_count != -1 and total_ask_count <= 0:
        # await websocket.close(1008, "errors.noAvailableTotalAskCount")
        raise WebsocketInvalidAskException("errors.noAvailableTotalAskCount")
    if model_ask_count != -1 and model_ask_count <= 0:
        # await websocket.close(1008, "errors.noAvailableModelAskCount")
        raise WebsocketInvalidAskException("errors.noAvailableModelAskCount")

    # 判断是否能新建对话
    async with get_async_session_context() as session:
        conv_count = await session.execute(
            select(func.count(BaseConversation.id)).filter(
                and_(BaseConversation.user_id == user.id, BaseConversation.is_valid,
                     BaseConversation.source == ask_request.source)))
        conv_count = conv_count.scalar()

    max_conv_count = source_setting.max_conv_count
    if ask_request.new_conversation and max_conv_count != -1 and conv_count >= max_conv_count:
        # await websocket.close(1008, "errors.maxConversationCountReached")
        raise WebsocketInvalidAskException("errors.maxConversationCountReached")

    # 判断是否允许上传文件
    if ask_request.openai_web_attachments and len(ask_request.openai_web_attachments) > 0:
        if ask_request.model != OpenaiWebChatModels.gpt_4_code_interpreter and \
                ask_request.model != OpenaiWebChatModels.gpt_4:
            raise WebsocketInvalidAskException("errors.uploadingNotAllowed",
                                               "only gpt-4 and gpt-4-code-interpreter models support uploading")
        if user.setting.openai_web.disable_uploading or config.openai_web.disable_uploading:
            raise WebsocketInvalidAskException("errors.uploadingNotAllowed", "uploading disabled")
    if ask_request.openai_web_multimodal_image_parts and len(ask_request.openai_web_multimodal_image_parts) > 0:
        if ask_request.model != OpenaiWebChatModels.gpt_4:
            raise WebsocketInvalidAskException("errors.uploadingNotAllowed", "only gpt-4 support uploading images")
        if user.setting.openai_web.disable_uploading or config.openai_web.disable_uploading:
            raise WebsocketInvalidAskException("errors.uploadingNotAllowed", "uploading disabled")


@router.websocket("/chat")
async def chat(websocket: WebSocket):
    """
    利用 WebSocket 实时更新 ChatGPT 回复
    """

    async def reply(response: AskResponse):
        if response.error_detail:
            response.error_detail = desensitize(response.error_detail)
        await websocket.send_json(jsonable_encoder(response))

    await websocket.accept()
    user_db = await websocket_auth(websocket)
    if user_db is None:
        await websocket.close(1008, "errors.unauthorized")
        return

    logger.info(f"{user_db.username} connected to websocket")
    websocket.scope["auth_user"] = user_db

    user = UserReadAdmin.model_validate(user_db)

    if user.setting.openai_web_chat_status != OpenaiWebChatStatus.idling:
        await websocket.close(1008, "errors.cannotConnectMoreThanOneClient")
        return

    params = await websocket.receive_json()

    try:
        ask_request = AskRequest.model_validate(params)
    except ValidationError as e:
        logger.warning(f"Invalid ask request: {e}")
        await reply(AskResponse(type=AskResponseType.error, error_detail=str(e)))
        await websocket.close(1007, "errors.invalidAskRequest")
        return

    # 检查限制
    try:
        await check_limits(user, ask_request)
    except WebsocketException as e:
        await reply(AskResponse(type=AskResponseType.error, tip=e.tip, error_detail=e.error_detail))
        await websocket.close(e.code, e.tip)
        return

    # 如果并非新建对话，则获取对话
    conversation = None
    conversation_id = None
    if not ask_request.new_conversation:
        assert ask_request.conversation_id is not None
        conversation_id = ask_request.conversation_id
        conversation = await _get_conversation_by_id(ask_request.conversation_id, user_db)

    request_start_time = datetime.now()

    websocket_code = 1001
    websocket_reason = "tips.terminated"

    is_completed = False
    is_canceled = False
    has_got_reply = False
    ask_start_time = None
    queueing_start_time = None
    queueing_end_time = None

    # 排队
    if ask_request.source == ChatSourceTypes.openai_web:
        if openai_web_manager.is_busy():
            await reply(AskResponse(
                type=AskResponseType.queueing,
                tip="tips.queueing"
            ))
        await change_user_chat_status(user.id, OpenaiWebChatStatus.queueing)
        queueing_start_time = time.time()
        await openai_web_manager.semaphore.acquire()
        queueing_end_time = time.time()
        # 如果 websocket 关闭了，则直接退出
        if websocket.state == WebSocketState.DISCONNECTED:
            await change_user_chat_status(user.id, OpenaiWebChatStatus.idling)
            await openai_web_manager.semaphore.release()
            logger.debug(f"{user.username} websocket disconnected while queueing")
            return

    # 在此之前应当没有任何副作用
    message = None

    try:
        # rev: 更改状态为 asking
        if ask_request.source == ChatSourceTypes.openai_web:
            await change_user_chat_status(user.id, OpenaiWebChatStatus.asking)

        await reply(AskResponse(
            type=AskResponseType.waiting,
            tip="tips.waiting"
        ))

        ask_start_time = time.time()

        manager = openai_web_manager if ask_request.source == ChatSourceTypes.openai_web else openai_api_manager

        # 设置 timeout
        if ask_request.source == ChatSourceTypes.openai_web:
            model = OpenaiWebChatModels(ask_request.model)
        else:
            model = OpenaiApiChatModels(ask_request.model)

        # stream 传输
        async for data in manager.complete(text_content=ask_request.text_content,
                                           conversation_id=ask_request.conversation_id,
                                           parent_message_id=ask_request.parent,
                                           model=model,
                                           plugin_ids=ask_request.openai_web_plugin_ids if ask_request.new_conversation else None,
                                           attachments=ask_request.openai_web_attachments,
                                           multimodal_image_parts=ask_request.openai_web_multimodal_image_parts,
                                           ):
            has_got_reply = True

            try:
                if ask_request.source == ChatSourceTypes.openai_web:
                    message = convert_openai_web_message(data)
                    if conversation_id is None:
                        conversation_id = data["conversation_id"]
                else:
                    assert isinstance(data, OpenaiApiChatMessage)
                    message = data
                    if conversation_id is None:
                        assert ask_request.new_conversation
                        conversation_id = uuid.uuid4()
            except Exception as e:
                logger.warning(f"convert message error: {e}")
                continue

            await reply(AskResponse(
                type=AskResponseType.message,
                conversation_id=conversation_id,
                message=message
            ))

        is_completed = True
    except ConnectionClosed as e:
        websocket_code = e.code
        websocket_reason = e.reason
        is_canceled = True
    except httpx.TimeoutException as e:
        logger.warning(str(e))
        await reply(AskResponse(
            type=AskResponseType.error,
            tip="errors.timout"
        ))
        websocket_code = 1001
        websocket_reason = "errors.timout"
    except OpenaiException as e:
        logger.error(str(e))
        error_detail_map = {
            401: "errors.openai.401",
            403: "errors.openai.403",
            404: "errors.openai.404",
            418: "errors.openai.418",
            429: "errors.openai.429",
            500: "errors.openai.500",
        }
        if e.code in error_detail_map:
            tip = error_detail_map[e.code]
        else:
            tip = "errors.openai.unknown"
        await reply(AskResponse(
            type=AskResponseType.error,
            tip=tip,
            error_detail=str(e)
        ))
        websocket_code = 1001
        websocket_reason = "errors.openaiResponseUnknownError"
    except HTTPError as e:
        logger.error(str(e))
        content = str(e)
        await reply(AskResponse(
            type=AskResponseType.error,
            tip="errors.httpError",
            error_detail=content
        ))
        websocket_code = 1014
        websocket_reason = "errors.httpError"
    except Exception as e:
        logger.error(str(e))
        await reply(AskResponse(
            type=AskResponseType.error,
            tip="errors.unknownError",
            error_detail=str(e)
        ))
        websocket_code = 1011
        websocket_reason = "errors.unknownError"

    finally:
        if ask_request.source == ChatSourceTypes.openai_web:
            openai_web_manager.semaphore.release()
            await change_user_chat_status(user.id, OpenaiWebChatStatus.idling)

    ask_stop_time = time.time()
    queueing_time = 0
    if queueing_start_time is not None:
        queueing_time = queueing_end_time - queueing_start_time
        queueing_time = round(queueing_time, 3)
    if ask_start_time is not None:
        ask_time = ask_stop_time - ask_start_time
        ask_time = round(ask_time, 3)
    else:
        ask_time = 0
    total_time = queueing_time + ask_time

    if is_completed:
        logger.debug(
            f"finished ask {conversation_id} ({ask_request.model}), user: {user.id}, "
            f"ask: {ask_time}s, total: {total_time}s")
        websocket_code = 1000
        websocket_reason = "tips.finished"
    elif is_canceled:
        if has_got_reply:
            logger.debug(
                f"canceled ask {conversation_id} ({ask_request.model}) while replying, user: {user.id}, "
                f"ask: {ask_time}s, total: {total_time}s")
        else:
            logger.debug(
                f"canceled ask {conversation_id} ({ask_request.model}) before replying, user: {user.id}, "
                f"total: {total_time}s")
    else:
        logger.debug(
            f"terminated ask {conversation_id} ({ask_request.model}) because of error")

    if has_got_reply:
        assert message is not None, "has_got_reply but message is None"

        if ask_request.source == ChatSourceTypes.openai_api:
            assert message.parent is not None, "message.parent is None"

            content = ask_request.text_content
            if isinstance(content, str):
                content = OpenaiApiChatMessageTextContent(content_type="text", text=content)

            ask_message = OpenaiApiChatMessage(
                source="openai_api",
                id=message.parent,
                role="user",
                create_time=request_start_time.astimezone(tz=timezone.utc),
                parent=ask_request.parent,
                children=[message.id],
                content=content
            )

            # 对于api新对话，添加历史记录到mongodb
            if ask_request.new_conversation:
                new_conv_history = OpenaiApiConversationHistoryDocument(
                    source="openai_api",
                    id=conversation_id,
                    title=ask_request.new_title or "New Chat",
                    create_time=request_start_time.astimezone(tz=timezone.utc),
                    update_time=datetime.now().astimezone(tz=timezone.utc),
                    mapping={
                        str(ask_message.id): ask_message,
                        str(message.id): message
                    },
                    current_node=message.id,
                    current_model=message.model
                )

                await new_conv_history.save()
                logger.debug(f"saved new api conversation history {conversation_id} to mongodb")
            else:
                # 更新mongodb历史记录
                conv_history = await OpenaiApiConversationHistoryDocument.get(conversation_id)
                assert conv_history is not None, f"update api: conversation history {conversation_id} is None"
                conv_history.update_time = datetime.now().astimezone(tz=timezone.utc)

                conv_history.mapping[str(ask_message.id)] = ask_message
                conv_history.mapping[str(message.id)] = message
                conv_history.current_node = str(message.id)
                conv_history.current_model = message.model

                if ask_message.parent is not None:
                    parent_message = conv_history.mapping.get(str(ask_message.parent))
                    assert parent_message is not None, f"update api: parent message {ask_message.parent} is None"
                    parent_message.children.append(message.id)
                    conv_history.mapping[str(ask_message.parent)] = parent_message
                await conv_history.save()

                logger.debug(f"updated api conversation history {conversation_id} to mongodb")

        # TODO: 扣除 credits

        async with get_async_session_context() as session:
            # 若新建了对话，则添加到数据库
            if ask_request.new_conversation:
                assert conversation_id is not None, "has_got_reply but conversation_id is None"

                # 设置默认标题
                if ask_request.source == ChatSourceTypes.openai_web and ask_request.new_title is not None and \
                        ask_request.new_title.strip() != "":
                    try:
                        await openai_web_manager.set_conversation_title(str(conversation_id), ask_request.new_title)
                    except Exception as e:
                        logger.warning(f"set_conversation_title error {e.__class__.__name__}: {str(e)}")

                current_time = datetime.now().astimezone(tz=timezone.utc)
                new_conv = BaseConversationSchema(
                    source=ask_request.source,
                    is_valid=True,
                    conversation_id=conversation_id,
                    title=ask_request.new_title,
                    user_id=user.id,
                    current_model=ask_request.model,
                    create_time=current_time,
                    update_time=current_time
                )
                conversation = BaseConversation(**new_conv.model_dump(exclude_unset=True))
                session.add(conversation)

            else:
                conversation = await session.get(BaseConversation, conversation.id)
                conversation.update_time = datetime.now().astimezone(tz=timezone.utc)
                # 更新当前模型
                if conversation.current_model != ask_request.model:
                    conversation.current_model = ask_request.model
                session.add(conversation)

            # 扣除对话次数
            source_setting = user.setting.openai_web if ask_request.source == ChatSourceTypes.openai_web else user.setting.openai_api

            total_ask_count = source_setting.total_ask_count
            model_ask_count = source_setting.per_model_ask_count.root.get(ask_request.model, -1)
            assert model_ask_count, "model_ask_count is None"
            if total_ask_count != -1 or model_ask_count != -1:

                if total_ask_count != -1:
                    assert total_ask_count > 0
                    source_setting.total_ask_count -= 1
                if model_ask_count != -1:
                    assert model_ask_count > 0
                    source_setting.per_model_ask_count.root[ask_request.model] = model_ask_count - 1

                user_db = await session.get(User, user.id)
                setattr(user_db.setting, ask_request.source, source_setting)

                session.add(user_db.setting)

            await session.commit()

            if ask_request.source == ChatSourceTypes.openai_web:
                meta = OpenaiWebAskLogMeta(source="openai_web", model=OpenaiWebChatModels(ask_request.model))
            else:
                meta = OpenaiApiAskLogMeta(source="openai_api", model=OpenaiApiChatModels(ask_request.model))

            # 写入到 scope 中，供统计
            await AskLogDocument(
                meta=meta,
                user_id=user.id,
                queueing_time=queueing_time,
                ask_time=ask_time,
                conversation_id=conversation_id,
            ).create()

    websocket.scope["ask_websocket_close_code"] = websocket_code
    websocket.scope["ask_websocket_close_reason"] = websocket_reason
    await websocket.close(websocket_code, websocket_reason)
