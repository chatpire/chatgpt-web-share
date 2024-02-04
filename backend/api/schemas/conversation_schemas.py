import datetime
import uuid
from enum import auto
from typing import Literal, Optional, Annotated, Union

from pydantic import ConfigDict, BaseModel, root_validator, validator, Field, model_validator
from strenum import StrEnum

from api.enums import ChatSourceTypes, OpenaiWebChatModels, OpenaiApiChatModels
from api.models.doc import OpenaiWebChatMessage, OpenaiApiChatMessage, \
    OpenaiWebChatMessageMultimodalTextContentImagePart, OpenaiWebChatMessageMetadataAttachment
from utils.logger import get_logger

logger = get_logger(__name__)


def _validate_model(_source: ChatSourceTypes, model: str | None):
    if model is None:
        return
    ignored_models = ["gpt-3.5-mobile", "gpt-4-mobile", "gpt-4-gizmo"]
    if model in ignored_models:
        return
    if _source == ChatSourceTypes.openai_web and model not in list(OpenaiWebChatModels):
        logger.warning(f"model {model} not in openai_web models: {'|'.join(list(OpenaiWebChatModels))}")
    elif _source == ChatSourceTypes.openai_api and model not in list(OpenaiApiChatModels):
        logger.warning(f"model {model} not in openai_api models: {'|'.join(list(OpenaiApiChatModels))}")


MAX_CONTEXT_MESSAGE_COUNT = 1000


class AskRequest(BaseModel):
    source: ChatSourceTypes
    model: str
    new_conversation: bool
    new_title: Optional[str] = None  # 为空则生成标题
    conversation_id: Optional[uuid.UUID] = None
    parent: Optional[uuid.UUID] = None
    api_context_message_count: Optional[int] = Field(None, ge=0, le=MAX_CONTEXT_MESSAGE_COUNT)
    text_content: str
    openai_web_plugin_ids: Optional[list[str]] = None
    openai_web_attachments: Optional[list[OpenaiWebChatMessageMetadataAttachment]] = None
    openai_web_multimodal_image_parts: Optional[list[OpenaiWebChatMessageMultimodalTextContentImagePart]] = None

    @model_validator(mode='before')
    @classmethod
    def check(cls, values):
        assert isinstance(values, dict)
        if values["new_conversation"] is True:
            assert values.get("conversation_id") is None, "new conversation can not specify conversation_id"
        else:
            assert values.get("conversation_id") is not None, "must specify conversation_id"
            assert values.get("parent") is not None, "must specify parent"
            assert values.get("new_title") is None, "can not specify new_title"
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
    error_detail: str | None = None


class BaseConversationSchema(BaseModel):
    id: int = -1
    source: ChatSourceTypes
    conversation_id: uuid.UUID | None = None
    source_id: Optional[str] = None  # TODO: hide this field for users
    title: str | None = None
    user_id: int | None = None
    is_valid: bool = True
    current_model: str | None = None
    create_time: datetime.datetime | None = None
    update_time: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def validate_current_model(cls, values):
        _validate_model(values["source"], values["current_model"])
        return values


class OpenaiWebConversationSchema(BaseConversationSchema):
    source: Literal["openai_web"]


class OpenaiApiConversationSchema(BaseConversationSchema):
    source: Literal["openai_api"]
