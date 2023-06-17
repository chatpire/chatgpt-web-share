import datetime
import uuid
from enum import auto
from typing import Literal, Optional, Annotated, Union

from pydantic import BaseModel, root_validator, validator, Field
from strenum import StrEnum

from api.enums import ChatSourceTypes, OpenaiWebChatModels, OpenaiApiChatModels
from api.models.doc import OpenaiWebChatMessage, OpenaiApiChatMessage
from utils.logger import get_logger

logger = get_logger(__name__)


def _validate_model(_source: ChatSourceTypes, model: str | None):
    if model is None:
        return None
    if _source == ChatSourceTypes.openai_web and model in list(OpenaiWebChatModels):
        return OpenaiWebChatModels(model)
    elif _source == ChatSourceTypes.openai_api and model in list(OpenaiApiChatModels):
        return OpenaiApiChatModels(model)
    else:
        logger.warning(f"unknown model: {model} for type {_source}")


class AskRequest(BaseModel):
    source: ChatSourceTypes
    model: str
    new_conversation: bool
    new_title: Optional[str] = None
    conversation_id: Optional[uuid.UUID] = None
    parent: Optional[uuid.UUID] = None
    api_context_message_count: int = Field(-1, ge=-1)
    content: str
    openai_web_plugin_ids: Optional[list[str]] = None

    @root_validator
    def check(cls, values):
        if values["new_conversation"] is True:
            assert values["conversation_id"] is None, "new conversation can not specify conversation_id"
        else:
            assert values["conversation_id"] is not None, "must specify conversation_id"
            assert values["parent"] is not None, "must specify parent"
            assert values["new_title"] is None, "can not specify new_title"
        _validate_model(values["source"], values["model"])
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
    message: Optional[
        Annotated[Union[OpenaiWebChatMessage, OpenaiApiChatMessage], Field(discriminator='source')]] = None
    error_detail: str = None


class BaseConversationSchema(BaseModel):
    id: int = -1
    source: ChatSourceTypes
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
        _validate_model(values["source"], v)
        return v


class OpenaiWebConversationSchema(BaseConversationSchema):
    source: Literal["openai_web"]


class OpenaiApiConversationSchema(BaseConversationSchema):
    source: Literal["openai_api"]
