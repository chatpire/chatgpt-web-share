import datetime
import uuid
from typing import Optional, Union, Any

from beanie import Document
from pydantic import BaseModel, Field

from api.enums import RevChatModels, ChatGPTSource, ApiChatModels


class RevChatMessageMetadata(BaseModel):
    # mapping[id].message.metadata 中的内容 加上 mapping[id].message 中的 weight, end_turn
    # 以下只有非用户回复有
    model_slug: Optional[Union[RevChatModels, str]]
    finish_details: Optional[dict[str, Any]]
    weight: Optional[float]
    end_turn: Optional[bool]


class ApiChatMessageMetadata(BaseModel):
    model: Optional[Union[ApiChatModels, str]]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    finish_reason: Optional[str]


class ChatMessage(BaseModel):
    id: uuid.UUID
    role: str  # rev: mapping[id].message.author.role: system, user, assistant
    create_time: datetime.datetime
    parent: Optional[uuid.UUID]
    children: list[uuid.UUID]
    content: str  # rev: mapping[id].message.content.parts[0]; mapping[id].message.content.content_type 为 text
    rev_metadata: Optional[RevChatMessageMetadata]  # rev only
    api_metadata: Optional[ApiChatMessageMetadata]  # api only


class ConversationHistory(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source: ChatGPTSource
    title: str
    create_time: datetime.datetime
    update_time: datetime.datetime
    mapping: dict[uuid.UUID, ChatMessage]
    current_node: uuid.UUID
    current_model: Optional[Union[RevChatModels, str]]  # rev: mapping[current_node].message.metadata.model_slug

    class Settings:
        name = "conversation_history"
