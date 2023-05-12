import uuid

import httpx

from api.conf import Config
from api.enums import ChatModel
from api.schema import ApiConversationSchema
from api.models import ChatMessage

config = Config()


class OpenAIManager:
    """
    OpenAI API Manager
    """

    def __init__(self, api_key):
        self.client = httpx.AsyncClient()

    async def ask(self, content: str, conversation: ApiConversationSchema = None,
                  parent: uuid.UUID = None, model: ChatModel = None):
        if not conversation:
            raise ValueError("conversation is required")
        model = model or ChatModel.gpt_3_5
        message = ChatMessage.new(role="user", content=content)
