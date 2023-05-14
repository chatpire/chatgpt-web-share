import datetime
import uuid
from enum import auto
from typing import Literal, Optional

from pydantic import BaseModel, root_validator, validator
from strenum import StrEnum

from api.enums import ChatSourceTypes, RevChatModels, ApiChatModels
from api.models.doc import ChatMessage


def _validate_model(_type: ChatSourceTypes, model: str):
    if _type == ChatSourceTypes.rev and model in list(RevChatModels):
        return RevChatModels(model)
    elif _type == ChatSourceTypes.api and model in list(ApiChatModels):
        return ApiChatModels(model)
    else:
        raise ValueError(f"invalid model {model} for type {_type}")


class AskRequest(BaseModel):
    type: ChatSourceTypes
    model: str
    new_conversation: bool
    new_title: Optional[str] = None
    conversation_id: Optional[uuid.UUID] = None
    parent: Optional[uuid.UUID] = None
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
        _validate_model(values["type"], values["model"])
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
    current_model: str | None
    create_time: datetime.datetime | None
    update_time: datetime.datetime | None

    class Config:
        orm_mode = True

    @validator("current_model")
    def validate_current_model(cls, v, values):
        _validate_model(values["type"], v)
        return v


class RevConversationSchema(BaseConversationSchema):
    type: Literal['rev'] = 'rev'


class ApiConversationSchema(BaseConversationSchema):
    type: Literal['api'] = 'api'
