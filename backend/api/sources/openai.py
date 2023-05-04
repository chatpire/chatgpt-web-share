import uuid

import httpx

from api.conf import Config
from api.enums import ApiChatModels
from api.models import ChatMessage
from api.schema import ApiConversationSchema

config = Config().config


class OpenAIManager:
    """
    OpenAI API Manager
    """

    def __init__(self, api_key):
        self.client = httpx.AsyncClient()

    async def ask(self, message: ChatMessage, model: ApiChatModels = None, conversation: ApiConversationSchema = None,
                  parent: uuid.UUID = None):
        model = model or ApiChatModels.gpt3
