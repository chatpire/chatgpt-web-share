import asyncio
import json
import uuid
from typing import AsyncGenerator

import httpx
import revChatGPT
from fastapi.encoders import jsonable_encoder
from pydantic import parse_obj_as, ValidationError
from revChatGPT.V1 import AsyncChatbot

from api.conf import Config, Credentials
from api.enums import RevChatModels, ChatSourceTypes
from api.exceptions import InvalidParamsException
from api.models.doc import RevChatMessageMetadata, RevConversationHistoryDocument, \
    RevConversationHistoryExtra, RevChatMessage, RevChatMessageTextContent, RevChatMessageCodeContent, \
    RevChatMessageTetherBrowsingDisplayContent, RevChatMessageTetherQuoteContent, RevChatMessageContent
from api.schema.openai_schemas import OpenAIChatPlugin, OpenAIChatPluginUserSettings
from utils.common import singleton_with_lock
from utils.logger import get_logger

config = Config()
credentials = Credentials()
logger = get_logger(__name__)


def convert_revchatgpt_message(item: dict, message_id: str = None) -> RevChatMessage | None:
    if not item.get("message"):
        return None
    if not not item["message"].get("author"):
        logger.debug(f"Parse message: Unknown author {item['message']['author']}")

    content = None
    fallback_content = None
    if item["message"].get("content"):
        content_type = item["message"]["content"].get("content_type")
        content_map = {
            "text": RevChatMessageTextContent,
            "code": RevChatMessageCodeContent,
            "tether_browsing_display": RevChatMessageTetherBrowsingDisplayContent,
            "tether_quote": RevChatMessageTetherQuoteContent
        }
        if content_type not in content_map:
            logger.debug(f"Parse message: Unknown content type {content_type}")
            fallback_content = item["message"]["content"]
        else:
            content = content_map[content_type](**item["message"]["content"])

    message_id = message_id or item["message"]["id"]
    result = RevChatMessage(
        id=message_id,  # 这里观察到message_id和mapping中的id不一样，暂时先使用mapping中的id
        role=item["message"]["author"]["role"],
        author_name=item["message"]["author"].get("name"),
        model=None,
        create_time=item["message"].get("create_time"),
        parent=item.get("parent"),
        children=item.get("children", []),
        content=content,
        metadata=RevChatMessageMetadata(
            type="rev",
            weight=item["message"].get("weight"),
            end_turn=item["message"].get("end_turn"),
            recipient=item["message"].get("recipient"),
            message_status=item["message"].get("status"),
            fallback_content=fallback_content,
        )
    )
    if "metadata" in item["message"] and item["message"]["metadata"] != {}:
        # result.metadata.finish_details = item["message"]["metadata"].get("finish_details")
        # result.metadata.invoked_plugin = item["message"]["metadata"].get("invoked_plugin")
        # result.metadata.command = item["message"]["metadata"].get("command")
        # result.metadata.args = item["message"]["metadata"].get("args")
        # result.metadata.status = item["message"]["metadata"].get("status")
        result.metadata = result.metadata.copy(
            update=item["message"]["metadata"]
        )
        result.metadata.cite_metadata = item["message"]["metadata"].get("_cite_metadata")
        model_code = item["message"]["metadata"].get("model_slug")
        result.model = RevChatModels.from_code(model_code) or model_code
    return result


def convert_mapping(mapping: dict[uuid.UUID, dict]) -> dict[str, RevChatMessage]:
    result = {}
    if not mapping:
        return result
    for key, item in mapping.items():
        message = convert_revchatgpt_message(item, str(key))
        if message:
            result[key] = message
    return {str(key): value for key, value in result.items()}


def get_latest_model_from_mapping(current_node_uuid: str | None,
                                  mapping: dict[str, RevChatMessage]) -> RevChatModels | None:
    model = None
    if not current_node_uuid:
        return model
    try:
        msg: RevChatMessage = mapping.get(current_node_uuid)
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
        error = revChatGPT.typings.Error(
            source="OpenAI",
            message=response.text,
            code=response.status_code,
        )
        raise error from ex


@singleton_with_lock
class RevChatGPTManager:
    """
    TODO: 解除 revChatGPT 依赖
    """

    def __init__(self):
        self.chatbot = AsyncChatbot({
            "access_token": credentials.chatgpt_access_token,
            "paid": config.revchatgpt.is_plus_account,
            "model": "text-davinci-002-render-sha",  # default model
        }, base_url=config.revchatgpt.chatgpt_base_url)
        self.semaphore = asyncio.Semaphore(1)

    def is_busy(self):
        return self.semaphore.locked()

    async def get_conversations(self):
        conversations = await self.chatbot.get_conversations(limit=80)
        return conversations

    async def get_conversation_history(self, conversation_id: uuid.UUID | str,
                                       refresh=True) -> RevConversationHistoryDocument:
        if not refresh:
            doc = await RevConversationHistoryDocument.get(conversation_id)
            if doc:
                return doc
        result = await self.chatbot.get_msg_history(conversation_id)
        result = jsonable_encoder(result)
        mapping = {}
        try:
            mapping = convert_mapping(result.get("mapping"))
        except Exception as e:
            raise InvalidParamsException(f"Failed to convert mapping: {e}")
        current_model = None
        if mapping.get(result.get("current_node")):
            current_model = get_latest_model_from_mapping(result["current_node"], mapping)
        doc = RevConversationHistoryDocument(
            id=conversation_id,
            title=result.get("title"),
            create_time=result.get("create_time"),
            update_time=result.get("update_time"),
            mapping=mapping,
            current_node=result.get("current_node"),
            current_model=current_model,
            rev_extra=RevConversationHistoryExtra(
                plugin_ids=result.get("plugin_ids"),
                moderation_results=result.get("moderation_results"),
            )
        )
        await doc.save()
        return doc

    async def clear_conversations(self):
        await self.chatbot.clear_conversations()

    async def ask(self, content: RevChatMessageContent, conversation_id: uuid.UUID = None, parent_id: uuid.UUID = None,
                  timeout=360, model: RevChatModels = None, plugin_ids: list[str] = None):

        model = model or RevChatModels.gpt_3_5

        if conversation_id or parent_id:
            assert parent_id and conversation_id, "parent_id must be set with conversation_id"
        else:
            parent_id = str(uuid.uuid4())

        if plugin_ids is not None and model != RevChatModels.gpt_4_plugins:
            raise InvalidParamsException("plugin_ids can only be set when model is gpt-4-plugins")

        messages = [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "author": {"role": "user"},
                "content": content,
            }
        ]

        data = {
            "action": "next",
            "messages": messages,
            "conversation_id": str(conversation_id) if conversation_id else None,
            "parent_message_id": str(parent_id) if parent_id else None,
            "model": model.code(),
            "history_and_training_disabled": False
        }
        if plugin_ids:
            data["plugin_ids"] = plugin_ids

        async with self.chatbot.session.stream(
                method="POST",
                url=f"{self.chatbot.base_url}conversation",
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
                    raise ValueError(f"Field missing. Details: {str(line)}")

                yield line

    async def delete_conversation(self, conversation_id: str):
        await self.chatbot.delete_conversation(conversation_id)

    async def set_conversation_title(self, conversation_id: str, title: str):
        """Hack change_title to set title in utf-8"""
        await self.chatbot.change_title(conversation_id, title)

    async def generate_conversation_title(self, conversation_id: str, message_id: str):
        """Hack gen_title to get title"""
        await self.chatbot.gen_title(conversation_id, message_id)

    def reset_chat(self):
        self.chatbot.reset_chat()

    async def get_plugin_manifests(self, statuses="approved", is_installed=None, offset=0, limit=250):
        params = {
            "statuses": statuses,
            "offset": offset,
            "limit": limit,
        }
        if is_installed is not None:
            params["is_installed"] = is_installed
        response = await self.chatbot.session.get(
            url=f"{self.chatbot.base_url}aip/p",
            params=params,
            timeout=config.revchatgpt.ask_timeout
        )
        await _check_response(response)
        return parse_obj_as(list[OpenAIChatPlugin], response.json().get("items"))

    async def change_plugin_user_settings(self, plugin_id: str, setting: OpenAIChatPluginUserSettings):
        response = await self.chatbot.session.patch(
            url=f"{self.chatbot.base_url}aip/p/{plugin_id}/user-settings",
            json=setting.dict(exclude_unset=True, exclude_none=True),
        )
        await _check_response(response)
        try:
            result = OpenAIChatPlugin.parse_obj(response.json())
            return result
        except ValidationError as e:
            logger.warning(f"Failed to parse plugin: {e}")
            raise e
