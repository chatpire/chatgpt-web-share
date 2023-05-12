import uuid

import httpx

from api.conf import Config
from api.enums import ApiChatModels
from api.models import ChatMessage
from api.schema import ApiConversationSchema

config = Config()


class OpenAIManager:
    """
    OpenAI API Manager
    """

    def __init__(self, api_key):
        self.client = httpx.AsyncClient()

    async def ask(self, content: str, conversation: ApiConversationSchema = None,
                  parent: uuid.UUID = None, model: ApiChatModels = None):
        if not conversation:
            raise ValueError("conversation is required")
        model = model or ApiChatModels.gpt_3_5_turbo
        message = ChatMessage.new(role="user", content=content)
