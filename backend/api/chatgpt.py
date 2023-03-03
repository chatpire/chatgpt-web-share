import json

from revChatGPT.V1 import Chatbot, BASE_URL
import asyncio
from revChatGPT.V1 import Error as ChatGPTError
from api.config import config


def chatbot_check_response(response):
    response.encoding = "utf-8"
    if response.status_code != 200:
        print(response.text)
        error = ChatGPTError()
        error.source = "OpenAI"
        error.code = response.status_code
        error.message = response.text
        raise error


class ChatGPTManager:
    def __init__(self):
        self.chatbot = Chatbot({
            "access_token": config.get("chatgpt_access_token"),
            "paid": config.get("chatgpt_paid"),
        })
        self.semaphore = asyncio.Semaphore(1)

    def is_busy(self):
        return self.semaphore.locked()

    def get_conversations(self):
        conversations = self.chatbot.get_conversations()
        return conversations

    def get_conversation_messages(self, conversation_id: str):
        # TODO: 使用 redis 缓存
        messages = self.chatbot.get_msg_history(conversation_id)
        return messages

    def clear_conversations(self):
        self.chatbot.clear_conversations()

    def get_ask_generator(self, message, use_paid=False, conversation_id: str = None, parrent_id: str = None,
                          timeout=360):
        self.chatbot.config["paid"] = use_paid
        return self.chatbot.ask(message, conversation_id, parrent_id, timeout)

    def delete_conversation(self, conversation_id: str):
        self.chatbot.delete_conversation(conversation_id)

    def set_conversation_title(self, conversation_id: str, title: str):
        """Hack change_title to set title in utf-8"""
        # self.chatbot.change_title(conversation_id, title)
        url = BASE_URL + f"api/conversation/{conversation_id}"
        data = json.dumps({"title": title}, ensure_ascii=False).encode("utf-8")
        response = self.chatbot.session.patch(url, data=data)
        chatbot_check_response(response)

    def generate_conversation_title(self, conversation_id: str, message_id: str):
        """Hack gen_title to get title"""
        # self.chatbot.gen_title(conversation_id, message_id)
        url = BASE_URL + f"api/conversation/gen_title/{conversation_id}"
        response = self.chatbot.session.post(
            url,
            data=json.dumps(
                {"message_id": message_id, "model": "text-davinci-002-render"},
            ),
        )
        chatbot_check_response(response)
        return response.json()
