import datetime
import uuid
from enum import auto
from typing import Literal, Optional

from pydantic import BaseModel, root_validator, validator
from strenum import StrEnum

from api.enums import ChatModel, ChatSourceTypes
from api.models import ChatMessage


class AskRequest(BaseModel):
    type: ChatSourceTypes
    new_conversation: bool
    new_title: Optional[str] = None
    conversation_id: Optional[uuid.UUID] = None
    parent: Optional[uuid.UUID] = None
    model: ChatModel
    api_context_message_count: int = -1
    content: str

    @root_validator
    def check(cls, values):
        if values["new_conversation"] is True:
            assert values["conversation_id"] is None, "new conversation can not specify conversation_id"
        else:
            assert values["conversation_id"] is not None, "must specify conversation_id"
            assert values["parent"] is not None, "must specify parent"
            assert values["new_title"] is None, "can not specify new_title"
        return values


class AskResponseType(StrEnum):
    waiting = auto()
    queueing = auto()
    message = auto()
    error = auto()


class AskResponse(BaseModel):
    type: AskResponseType
    tip: str = None
    conversation_id: uuid.UUID = None
    message: ChatMessage = None
    error_detail: str = None


class BaseConversationSchema(BaseModel):
    id: int = -1
    type: ChatSourceTypes
    conversation_id: uuid.UUID | None
    title: str | None
    user_id: int | None
    is_valid: bool = True
    current_model: ChatModel | None
    create_time: datetime.datetime | None
    update_time: datetime.datetime | None

    class Config:
        orm_mode = True


class RevConversationSchema(BaseConversationSchema):
    type: Literal['rev'] = 'rev'


class ApiConversationSchema(BaseConversationSchema):
    type: Literal['api'] = 'api'
