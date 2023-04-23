import api.globals as g
from fastapi.encoders import jsonable_encoder
from revChatGPT.V1 import AsyncChatbot
import asyncio
from api.enums import RevChatModels
from api.conf import Config
from utils.conv import get_model_name_from_conv

_config = Config().get_config()


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

    async def get_conversation_messages(self, conversation_id: str):
        # TODO: 使用 redis 缓存
        messages = await self.chatbot.get_msg_history(conversation_id)
        messages = jsonable_encoder(messages)
        model_name = get_model_name_from_conv(messages)
        messages["model_name"] = model_name or RevChatModels.unknown.value
        return messages

    async def clear_conversations(self):
        await self.chatbot.clear_conversations()

    def ask(self, message, conversation_id: str = None, parent_id: str = None,
            timeout=360, model_name: RevChatModels = None):
        model = None
        if model_name is not None and model_name != RevChatModels.unknown:
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
