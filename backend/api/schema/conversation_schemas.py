import datetime
import uuid
from typing import Literal

from pydantic import BaseModel

from api.enums import ChatModel, ChatSourceTypes
from api.models import ConversationHistoryDocument


class BaseConversationSchema(BaseModel):
    id: int = -1
    type: ChatSourceTypes
    conversation_id: uuid.UUID | None
    title: str | None
    user_id: int | None
    is_valid: bool = True
    model_name: ChatModel | None
    create_time: datetime.datetime | None
    update_time: datetime.datetime | None

    class Config:
        orm_mode = True


class RevConversationSchema(BaseConversationSchema):
    type: Literal['rev']


class ApiConversationSchema(BaseConversationSchema):
    type: Literal['api']
