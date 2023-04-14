import api.globals as g
import os

if g.config.get("chatgpt_base_url"):
    os.environ["CHATGPT_BASE_URL"] = g.config.get("chatgpt_base_url")

from fastapi.encoders import jsonable_encoder
from revChatGPT.V1 import AsyncChatbot
import asyncio
from api.enums import ChatModels
from utils.common import get_conversation_model
from api.database import get_async_session_context
from sqlalchemy.future import select
from api.models import Api, User, UserApi, Conversation
import requests
import openai
import json
from utils.logger import get_logger
logger = get_logger(__name__)

def _uuid():
    import uuid
    return str(uuid.uuid4())

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
            timeout=360, model_name: ChatModels = None, _: Conversation = None):
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

class ChatGptApiManager:
    def __init__(self, api_type: str = "openai", api_key: str = "", endpoint: str = "") -> None:
        self.api_type = api_type
        if api_type == "openai" and not endpoint:
            self.endpoint = "https://api.openai.com/v1/chat/completions"
        else:
            self.endpoint = endpoint
        
        if api_type == "openai":
            self._headers = {
                "Authorization": "Bearer " + api_key
            }
        else:
            self._headers = {
                "api-key": api_key
            }
        self._headers["Content-Type"] = "application/json"
        self.semaphore = asyncio.Semaphore(10000)
        
    def is_busy(self):
        return self.semaphore.locked() 
    
    async def ask(self, message, conversation_id: str = None, parent_id: str = None,
            timeout=360, model_name: ChatModels = None, converstaion: Conversation = None):
            history = []
            conversation_id = _uuid()
            if converstaion:
                history = converstaion.state
                conversation_id = converstaion.conversation_id
            history.append({
                "role": "user", 
                "content": message
            })
            data = {
                "messages": history,
                "stream": True,
                "temperature": 0.6,
            }
            if self.api_type == "openai":
                data["model"] = model_name.value.replace("openai-", "")
            else:
                data.update(**{"presence_penalty": 0,
                "top_p": 1,
                "n": 1,
                "max_tokens": 1000,
                "logit_bias": {}})
            r = requests.post(self.endpoint, json=data, headers=self._headers, stream=True)
            parent_id = _uuid()
            message = ''
            for vo in r.iter_lines():
                vo = vo.decode("utf-8")
                if vo != "[DONE]":
                    try:
                        vo = json.loads(vo[6:])
                    except:
                        continue
                    message += vo.get("choices", [{}])[0].get("delta", {}).get("content", "").lstrip('\n')
                    yield {
                        "conversation_id": conversation_id,
                        "parent_id": parent_id,
                        "model": vo['model'],
                        "message": message
                    }
    async def delete_conversation(self, conversation_id: str):
        pass

    async def set_conversation_title(self, conversation_id: str, title: str):
        pass
    
    async def generate_conversation_title(self, conversation_id: str, message_id: str):
        pass

    def reset_chat(self):
        pass

chatgpt_manager = ChatGPTManager()
