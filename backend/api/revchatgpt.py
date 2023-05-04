import asyncio
import uuid

from fastapi.encoders import jsonable_encoder
from revChatGPT.V1 import AsyncChatbot

from api.conf import Config
from api.enums import RevChatModels
from api.models import RevChatMessageMetadata, ChatMessage, ConversationHistory

_config = Config().get_config()


def convert_mapping(mapping: dict[uuid.UUID, dict]) -> dict[uuid.UUID, ChatMessage]:
    result = {}
    if not mapping:
        return result
    for k, v in mapping.items():
        if not v.get("message"):
            continue
        content = ""
        if v["message"].get("content"):
            if v["message"]["content"].get("content_type") == "text":
                content = v["message"]["content"]["parts"][0]
            else:
                raise ValueError(
                    f"!! Unknown message content type: {v['message']['content']['content_type']} in message {k}")
        result[k] = ChatMessage(
            id=k,  # TODO 这里观察到message_id和mapping中的id不一样，暂时先使用mapping中的id
            role=v["message"]["author"]["role"],
            create_time=v["message"].get("create_time"),
            parent=v.get("parent"),
            children=v.get("children", []),
            content=content
        )
        if "metadata" in v["message"] and v["message"]["metadata"] != {}:
            result[k].rev_metadata = RevChatMessageMetadata(
                model_slug=v["message"]["metadata"].get("model_slug"),
                finish_details=v["message"]["metadata"].get("finish_details"),
                weight=v["message"].get("weight"),
                end_turn=v["message"].get("end_turn"),
            )
    return result


def get_last_model_name_from_mapping(current_node_uuid: uuid.UUID, mapping: dict[uuid.UUID, ChatMessage]):
    model_name = None
    try:
        current = mapping.get(current_node_uuid)
        while current:
            if current.rev_metadata and current.rev_metadata.model_slug:
                model_name = current.rev_metadata.model_slug
                break
            current = mapping.get(current.parent)
    finally:
        return model_name


class ChatGPTManager:
    def __init__(self):
        self.chatbot = AsyncChatbot({
            "access_token": _config.credentials.chatgpt_account_access_token,
            "paid": _config.chatgpt.is_plus_account,
            "model": "text-davinci-002-render-sha",  # default model
        }, base_url=_config.chatgpt.chatgpt_base_url)
        self.semaphore = asyncio.Semaphore(1)

    def is_busy(self):
        return self.semaphore.locked()

    async def get_conversations(self):
        conversations = await self.chatbot.get_conversations(limit=80)
        return conversations

    async def get_conversation_history(self, conversation_id: uuid.UUID | str) -> ConversationHistory:
        result = await self.chatbot.get_msg_history(conversation_id)
        result = jsonable_encoder(result)
        mapping = convert_mapping(result.get("mapping"))
        current_model = None
        if mapping.get(result.get("current_node")):
            current_model = get_last_model_name_from_mapping(result["current_node"], mapping)
        doc = ConversationHistory(
            id=conversation_id,
            title=result.get("title"),
            create_time=result.get("create_time"),
            update_time=result.get("update_time"),
            mapping=mapping,
            current_node=result.get("current_node"),
            current_model=current_model,
        )
        return doc

    async def clear_conversations(self):
        await self.chatbot.clear_conversations()

    def ask(self, message, conversation_id: str = None, parent_id: str = None,
            timeout=360, model_name: RevChatModels = None):
        model = None
        if model_name is not None:
            model = model_name.value
        return self.chatbot.ask(message, conversation_id=conversation_id, parent_id=parent_id, model=model,
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


chatgpt_manager = ChatGPTManager()
