import asyncio
import uuid
from typing import Dict
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from revChatGPT.V1 import AsyncChatbot

from api.conf import Config, Credentials
from api.enums import ChatModel, ChatSourceTypes
from api.models import RevChatMessageMetadata, ChatMessage, ConversationHistoryDocument

config = Config()
credentials = Credentials()


def convert_mapping(mapping: dict[uuid.UUID, dict]) -> dict[str, ChatMessage]:
    result = {}
    if not mapping:
        return result
    for key, item in mapping.items():
        if not item.get("message"):
            continue
        content = ""
        if item["message"].get("content"):
            if item["message"]["content"].get("content_type") == "text":
                content = item["message"]["content"]["parts"][0]
            else:
                raise ValueError(
                    f"!! Unknown message content type: {item['message']['content']['content_type']} in message {key}")
        result[key] = ChatMessage(
            id=key,  # 这里观察到message_id和mapping中的id不一样，暂时先使用mapping中的id
            role=item["message"]["author"]["role"],
            create_time=item["message"].get("create_time"),
            parent=item.get("parent"),
            children=item.get("children", []),
            content=content
        )
        if "metadata" in item["message"] and item["message"]["metadata"] != {}:
            result[key].rev_metadata = RevChatMessageMetadata(
                model=item["message"]["metadata"].get("model_slug"),
                finish_details=item["message"]["metadata"].get("finish_details"),
                weight=item["message"].get("weight"),
                end_turn=item["message"].get("end_turn"),
            )
    return {str(key): value for key, value in result.items()}


def get_latest_model_from_mapping(current_node_uuid: str, mapping: dict[str, ChatMessage]) -> ChatModel:
    model_name = None
    try:
        current = mapping.get(current_node_uuid)
        while current:
            if current.rev_metadata and current.rev_metadata.model:
                model_name = current.rev_metadata.model
                break
            current = mapping.get(str(current.parent))
    finally:
        return ChatModel.from_code(model_name)


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
        mapping = convert_mapping(result.get("mapping"))
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

    def ask(self, message: str, conversation_id: str = None, parent_id: str = None,
            timeout=360, model_name: ChatModel = None):
        model = model_name or ChatModel.gpt_3_5
        return self.chatbot.ask(message, conversation_id=conversation_id, parent_id=parent_id,
                                model=model.code(ChatSourceTypes.rev),
                                timeout=timeout)

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
