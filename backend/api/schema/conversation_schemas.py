import datetime
import uuid
from typing import Literal

from pydantic import BaseModel

from api.enums import RevChatModels, ApiChatModels
from api.models import ConversationHistoryDocument


class BaseConversationSchema(BaseModel):
    id: int = -1
    conv_type: str
    conversation_id: uuid.UUID | None
    title: str | None
    user_id: int | None
    is_valid: bool = True
    model_name: str | None
    create_time: datetime.datetime | None
    update_time: datetime.datetime | None

    class Config:
        orm_mode = True


class RevConversationSchema(BaseConversationSchema):
    conv_type: Literal['rev'] = "rev"
    model_name: RevChatModels | None


class ApiConversationSchema(BaseConversationSchema):
    conv_type: Literal['api'] = "api"
    model_name: ApiChatModels | None


class ConversationHistoryResponse(BaseModel):
    is_cached: bool
    history: ConversationHistoryDocument
