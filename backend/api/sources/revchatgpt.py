import asyncio
import json
import uuid
from typing import AsyncGenerator

import httpx
import revChatGPT
from fastapi.encoders import jsonable_encoder
from revChatGPT.V1 import AsyncChatbot

from api.conf import Config, Credentials
from api.enums import RevChatModels, ChatSourceTypes
from api.exceptions import InvalidParamsException
from api.models.doc import RevChatMessageMetadata, ConversationHistoryDocument, ChatMessage
from utils.common import singleton_with_lock

config = Config()
credentials = Credentials()


def convert_revchatgpt_message(item: dict, message_id: str = None) -> ChatMessage | None:
    if not item.get("message"):
        return None
    content = ""
    message_id = message_id or item["message"]["id"]
    if item["message"].get("content"):
        if item["message"]["content"].get("content_type") == "text":
            content = item["message"]["content"]["parts"][0]
        else:
            raise ValueError(
                f"!! Unknown message content type: {item['message']['content']['content_type']} in message {message_id}")
    result = ChatMessage(
        id=message_id,  # 这里观察到message_id和mapping中的id不一样，暂时先使用mapping中的id
        role=item["message"]["author"]["role"],
        create_time=item["message"].get("create_time"),
        parent=item.get("parent"),
        children=item.get("children", []),
        content=content
    )
    if "metadata" in item["message"] and item["message"]["metadata"] != {}:
        result.model = RevChatModels.from_code(item["message"]["metadata"].get("model_slug"))
        result.rev_metadata = RevChatMessageMetadata(
            finish_details=item["message"]["metadata"].get("finish_details"),
            weight=item["message"].get("weight"),
            end_turn=item["message"].get("end_turn"),
        )
    return result


def convert_mapping(mapping: dict[uuid.UUID, dict]) -> dict[str, ChatMessage]:
    result = {}
    if not mapping:
        return result
    for key, item in mapping.items():
        message = convert_revchatgpt_message(item, str(key))
        if message:
            result[key] = message
    return {str(key): value for key, value in result.items()}


def get_latest_model_from_mapping(current_node_uuid: str, mapping: dict[str, ChatMessage]) -> RevChatModels | None:
    model = None
    try:
        msg: ChatMessage = mapping.get(current_node_uuid)
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
                                       refresh=True) -> ConversationHistoryDocument:
        if not refresh:
            doc = await ConversationHistoryDocument.get(conversation_id)
            if doc:
                return doc
        result = await self.chatbot.get_msg_history(conversation_id)
        result = jsonable_encoder(result)
        mapping = {}
        try:
            mapping = convert_mapping(result.get("mapping"))
        except Exception as e:
            raise InvalidParamsException(f"!! Failed to convert mapping: {e}")
        current_model = None
        if mapping.get(result.get("current_node")):
            current_model = get_latest_model_from_mapping(result["current_node"], mapping)
        doc = ConversationHistoryDocument(
            id=conversation_id,
            type="rev",
            title=result.get("title"),
            create_time=result.get("create_time"),
            update_time=result.get("update_time"),
            mapping=mapping,
            current_node=result.get("current_node"),
            current_model=current_model,
        )
        await doc.save()
        return doc

    async def clear_conversations(self):
        await self.chatbot.clear_conversations()

    async def ask(self, content: str, conversation_id: uuid.UUID = None, parent_id: uuid.UUID = None,
                  timeout=360, model: RevChatModels = None):

        model = model or RevChatModels.gpt_3_5

        if conversation_id or parent_id:
            assert parent_id and conversation_id, "parent_id must be set with conversation_id"
        else:
            parent_id = str(uuid.uuid4())

        messages = [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "author": {"role": "user"},
                "content": {"content_type": "text", "parts": [content]},
            }
        ]

        data = {
            "action": "next",
            "messages": messages,
            "conversation_id": str(conversation_id) if conversation_id else None,
            "parent_message_id": str(parent_id) if parent_id else None,
            "model": model.code()
        }

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
