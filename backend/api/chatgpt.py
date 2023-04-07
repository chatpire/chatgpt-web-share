import api.globals as g
import os

if g.config.get("chatgpt_base_url"):
    os.environ["CHATGPT_BASE_URL"] = g.config.get("chatgpt_base_url")

from fastapi.encoders import jsonable_encoder
from revChatGPT.V1 import AsyncChatbot
import asyncio
from api.enums import ChatModels
from utils.common import get_conversation_model


class ChatGPTManager:
    def __init__(self):
        self.chatbot = AsyncChatbot({
            "access_token": g.config.get("chatgpt_access_token"),
            "paid": g.config.get("chatgpt_paid"),
        })
        self.semaphore = asyncio.Semaphore(1)

    def is_busy(self):
        return self.semaphore.locked()

    async def get_conversations(self):
        conversations = await self.chatbot.get_conversations()
        return conversations

    async def get_conversation_messages(self, conversation_id: str):
        # TODO: 使用 redis 缓存
        messages = await self.chatbot.get_msg_history(conversation_id)
        messages = jsonable_encoder(messages)
        model_name = get_conversation_model(messages)
        messages["model_name"] = model_name or ChatModels.unknown.value
        return messages

    async def clear_conversations(self):
        await self.chatbot.clear_conversations()

    def ask(self, message, conversation_id: str = None, parent_id: str = None,
            timeout=360, model_name: ChatModels = None):
        if model_name is not None and model_name != ChatModels.unknown:
            self.chatbot.config["model"] = model_name.value
        return self.chatbot.ask(message, conversation_id, parent_id, timeout)

    async def delete_conversation(self, conversation_id: str):
        await self.chatbot.delete_conversation(conversation_id)

    async def set_conversation_title(self, conversation_id: str, title: str):
        """Hack change_title to set title in utf-8"""
        await self.chatbot.change_title(conversation_id, title)
        # url = BASE_URL + f"api/conversation/{conversation_id}"
        # data = json.dumps({"title": title}, ensure_ascii=False).encode("utf-8")
        # response = self.chatbot.session.patch(url, data=data)
        # chatbot_check_response(response)

    async def generate_conversation_title(self, conversation_id: str, message_id: str):
        """Hack gen_title to get title"""
        await self.chatbot.gen_title(conversation_id, message_id)
        # url = BASE_URL + f"api/conversation/gen_title/{conversation_id}"
        # response = self.chatbot.session.post(
        #     url,
        #     data=json.dumps(
        #         {"message_id": message_id, "model": "text-davinci-002-render"},
        #     ),
        # )
        # chatbot_check_response(response)
        # return response.json()

    def reset_chat(self):
        self.chatbot.reset_chat()
        if self.chatbot.config.get("model"):
            self.chatbot.config["model"] = None


chatgpt_manager = ChatGPTManager()
