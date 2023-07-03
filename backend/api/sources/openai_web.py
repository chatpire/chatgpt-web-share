import asyncio
import json
import uuid
from typing import AsyncGenerator

import httpx
from fastapi.encoders import jsonable_encoder
from pydantic import parse_obj_as, ValidationError

from api.conf import Config, Credentials
from api.enums import OpenaiWebChatModels, ChatSourceTypes
from api.exceptions import InvalidParamsException, OpenaiWebException
from api.models.doc import OpenaiWebChatMessageMetadata, OpenaiWebConversationHistoryDocument, \
    OpenaiWebConversationHistoryMeta, OpenaiWebChatMessage, OpenaiWebChatMessageTextContent, \
    OpenaiWebChatMessageCodeContent, \
    OpenaiWebChatMessageTetherBrowsingDisplayContent, OpenaiWebChatMessageTetherQuoteContent, \
    OpenaiWebChatMessageContent, \
    OpenaiWebChatMessageSystemErrorContent, OpenaiWebChatMessageStderrContent
from api.schemas.openai_schemas import OpenaiChatPlugin, OpenaiChatPluginUserSettings
from utils.common import singleton_with_lock
from utils.logger import get_logger

config = Config()
credentials = Credentials()
logger = get_logger(__name__)


def convert_revchatgpt_message(item: dict, message_id: str = None) -> OpenaiWebChatMessage | None:
    if not item.get("message"):
        return None
    if not item["message"].get("author"):
        logger.debug(f"Parse message {message_id}: Unknown author")

    content = None
    fallback_content = None
    if item["message"].get("content"):
        content_type = item["message"]["content"].get("content_type")
        content_map = {
            "text": OpenaiWebChatMessageTextContent,
            "code": OpenaiWebChatMessageCodeContent,
            "stderr": OpenaiWebChatMessageStderrContent,
            "tether_browsing_display": OpenaiWebChatMessageTetherBrowsingDisplayContent,
            "tether_quote": OpenaiWebChatMessageTetherQuoteContent,
            "system_error": OpenaiWebChatMessageSystemErrorContent
        }
        if content_type not in content_map:
            logger.debug(f"Parse message: Unknown content type {content_type}")
            fallback_content = item["message"]["content"]
        else:
            content = content_map[content_type](**item["message"]["content"])

    message_id = message_id or item["message"]["id"]
    result = OpenaiWebChatMessage(
        source="openai_web",
        id=message_id,  # 这里观察到message_id和mapping中的id不一样，暂时先使用mapping中的id
        role=item["message"]["author"]["role"],
        author_name=item["message"]["author"].get("name"),
        model=None,
        create_time=item["message"].get("create_time"),
        parent=item.get("parent"),
        children=item.get("children", []),
        content=content,
        metadata=OpenaiWebChatMessageMetadata(
            source="openai_web",
            weight=item["message"].get("weight"),
            end_turn=item["message"].get("end_turn"),
            recipient=item["message"].get("recipient"),
            message_status=item["message"].get("status"),
            fallback_content=fallback_content,
        )
    )
    if "metadata" in item["message"] and item["message"]["metadata"] != {}:
        result.metadata = result.metadata.copy(
            update=item["message"]["metadata"]
        )
        model_code = item["message"]["metadata"].get("model_slug")
        result.model = OpenaiWebChatModels.from_code(model_code) or model_code
    return result


def convert_mapping(mapping: dict[uuid.UUID, dict]) -> dict[str, OpenaiWebChatMessage]:
    result = {}
    if not mapping:
        return result
    for key, item in mapping.items():
        message = convert_revchatgpt_message(item, str(key))
        if message:
            result[key] = message
    return {str(key): value for key, value in result.items()}


def get_latest_model_from_mapping(current_node_uuid: str | None,
                                  mapping: dict[str, OpenaiWebChatMessage]) -> OpenaiWebChatModels | None:
    model = None
    if not current_node_uuid:
        return model
    try:
        msg: OpenaiWebChatMessage = mapping.get(current_node_uuid)
        while msg:
            if msg.model:
                model = msg.model
                break
            msg = mapping.get(str(msg.parent))
    finally:
        return model


def _check_fields(data: dict) -> bool:
    try:
        data["message"]["content"]
    except (TypeError, KeyError):
        return False
    return True


async def _check_response(response: httpx.Response) -> None:
    # 改成自带的错误处理
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        await response.aread()
        error = OpenaiWebException(
            message=response.text,
            code=response.status_code,
        )
        raise error from ex


def make_session() -> httpx.AsyncClient:
    if config.openai_web.proxy is not None:
        proxies = {
            "http://": config.openai_web.proxy,
            "https://": config.openai_web.proxy,
        }
        session = httpx.AsyncClient(proxies=proxies)
    else:
        session = httpx.AsyncClient()
    session.headers.clear()
    session.headers.update(
        {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {credentials.openai_web_access_token}",
            "Content-Type": "application/json",
            "X-Openai-Assistant-App-Id": "",
            "Connection": "close",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://chat.openai.com/chat",
        },
    )
    return session


@singleton_with_lock
class OpenaiWebChatManager:
    """
    TODO: 解除 revChatGPT 依赖
    """

    def __init__(self):
        self.session = make_session()
        self.semaphore = asyncio.Semaphore(1)

    def is_busy(self):
        return self.semaphore.locked()

    def reset_session(self):
        self.session = make_session()

    async def get_conversations(self, timeout=None):
        all_conversations = []
        offset = 0
        limit = 80
        while True:
            url = f"{config.openai_web.chatgpt_base_url}conversations?offset={offset}&limit={limit}"
            if timeout is None:
                timeout = httpx.Timeout(config.openai_web.common_timeout)
            response = await self.session.get(url, timeout=timeout)
            await _check_response(response)
            data = json.loads(response.text)
            conversations = data["items"]
            if len(conversations):
                all_conversations.extend(conversations)
            else:
                break
            offset += 80
        return all_conversations

    async def get_conversation_history(self, conversation_id: uuid.UUID | str) -> OpenaiWebConversationHistoryDocument:
        url = f"{config.openai_web.chatgpt_base_url}conversation/{conversation_id}"
        response = await self.session.get(url, timeout=None)
        response.encoding = 'utf-8'
        await _check_response(response)
        result = json.loads(response.text)
        mapping = {}
        try:
            mapping = convert_mapping(result.get("mapping"))
        except Exception as e:
            raise InvalidParamsException(f"Failed to convert mapping: {e}")
        current_model = None
        if mapping.get(result.get("current_node")):
            current_model = get_latest_model_from_mapping(result["current_node"], mapping)
        doc = OpenaiWebConversationHistoryDocument(
            source="openai_web",
            id=conversation_id,
            title=result.get("title"),
            create_time=result.get("create_time"),
            update_time=result.get("update_time"),
            mapping=mapping,
            current_node=result.get("current_node"),
            current_model=current_model,
            metadata=OpenaiWebConversationHistoryMeta(
                source="openai_web",
                plugin_ids=result.get("plugin_ids"),
                moderation_results=result.get("moderation_results"),
            )
        )
        await doc.save()
        return doc

    async def clear_conversations(self):
        # await self.chatbot.clear_conversations()
        url = f"{config.openai_web.chatgpt_base_url}conversations"
        response = await self.session.patch(url, data={"is_visible": False})
        await _check_response(response)

    async def ask(self, content: str, conversation_id: uuid.UUID = None, parent_id: uuid.UUID = None,
                  model: OpenaiWebChatModels = None, plugin_ids: list[str] = None, **_kwargs):

        model = model or OpenaiWebChatModels.gpt_3_5

        if conversation_id or parent_id:
            assert parent_id and conversation_id, "parent_id must be set with conversation_id"
        else:
            parent_id = str(uuid.uuid4())

        if plugin_ids is not None and model != OpenaiWebChatModels.gpt_4_plugins:
            raise InvalidParamsException("plugin_ids can only be set when model is gpt-4-plugins")


        if content == ":continue":
            data = {
                "action": "continue",
                "conversation_id": str(conversation_id) if conversation_id else None,
                "parent_message_id": str(parent_id) if parent_id else None,
                "model": model.code(),
                "timezone_offset_min": -480,
                "history_and_training_disabled": False,
            }
        else:
            content = OpenaiWebChatMessageTextContent(
                content_type="text", parts=[content]
            )

            messages = [
                {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "author": {"role": "user"},
                    "content": content.dict(),
                }
            ]

            data = {
                "action": "next",
                "messages": messages,
                "conversation_id": str(conversation_id) if conversation_id else None,
                "parent_message_id": str(parent_id) if parent_id else None,
                "model": model.code(),
                "history_and_training_disabled": False,
                "arkose_token": None
            }
        if plugin_ids and conversation_id is None:
            data["plugin_ids"] = plugin_ids

        timeout = httpx.Timeout(Config().openai_web.common_timeout, read=Config().openai_web.ask_timeout)

        async with self.session.stream(
                method="POST",
                url=f"{config.openai_web.chatgpt_base_url}conversation",
                data=json.dumps(data),
                timeout=timeout,
        ) as response:
            await _check_response(response)
            async for line in response.aiter_lines():
                if not line or line is None:
                    continue
                if "data: " in line:
                    line = line[6:]
                if "[DONE]" in line:
                    break

                try:
                    line = json.loads(line)
                except json.decoder.JSONDecodeError:
                    continue
                if not _check_fields(line):
                    if "error" in line:
                        raise OpenaiWebException(line["error"])
                    else:
                        logger.warning(f"Field missing. Details: {str(line)}")
                        continue

                yield line

    async def delete_conversation(self, conversation_id: str):
        # await self.chatbot.delete_conversation(conversation_id)
        url = f"{config.openai_web.chatgpt_base_url}conversation/{conversation_id}"
        response = await self.session.patch(url, data='{"is_visible": false}')
        await _check_response(response)

    async def set_conversation_title(self, conversation_id: str, title: str):
        url = f"{config.openai_web.chatgpt_base_url}conversation/{conversation_id}"
        response = await self.session.patch(url, data=f'{{"title": "{title}"}}')
        await _check_response(response)

    async def generate_conversation_title(self, conversation_id: str, message_id: str):
        url = f"{config.openai_web.chatgpt_base_url}conversation/gen_title/{conversation_id}"
        response = await self.session.post(
            url,
            data=json.dumps({"message_id": message_id, "model": "text-davinci-002-render"}),
        )
        await _check_response(response)

    async def get_plugin_manifests(self, statuses="approved", is_installed=None, offset=0, limit=250):
        if not config.openai_web.is_plus_account:
            raise InvalidParamsException("errors.notPlusChatgptAccount")
        params = {
            "statuses": statuses,
            "offset": offset,
            "limit": limit,
        }
        if is_installed is not None:
            params["is_installed"] = is_installed
        response = await self.session.get(
            url=f"{config.openai_web.chatgpt_base_url}aip/p",
            params=params,
            timeout=config.openai_web.ask_timeout
        )
        await _check_response(response)
        return parse_obj_as(list[OpenaiChatPlugin], response.json().get("items"))

    async def change_plugin_user_settings(self, plugin_id: str, setting: OpenaiChatPluginUserSettings):
        if not config.openai_web.is_plus_account:
            raise InvalidParamsException("errors.notPlusChatgptAccount")
        response = await self.session.patch(
            url=f"{config.openai_web.chatgpt_base_url}aip/p/{plugin_id}/user-settings",
            json=setting.dict(exclude_unset=True, exclude_none=True),
        )
        await _check_response(response)
        try:
            result = OpenaiChatPlugin.parse_obj(response.json())
            return result
        except ValidationError as e:
            logger.warning(f"Failed to parse plugin: {e}")
            raise e
