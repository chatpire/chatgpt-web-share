import datetime
import uuid
from typing import Optional, Union, Any, Literal

from beanie import Document
from pydantic import BaseModel, Field

from api.enums import ChatModel


class RevChatMessageMetadata(BaseModel):
    # mapping[id].message.metadata 中的内容 加上 mapping[id].message 中的 weight, end_turn
    # 以下只有assistant有
    finish_details: Optional[dict[str, Any]]
    weight: Optional[float]
    end_turn: Optional[bool]


class ApiChatMessageMetadata(BaseModel):
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    finish_reason: Optional[str]


class ChatMessage(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    role: str  # rev: mapping[id].message.author.role: system, user, assistant
    model: Optional[Union[ChatModel, str]]  # rev: mapping[id].message.metadata.model_slug -> ChatModel
    create_time: datetime.datetime = Field(default_factory=datetime.datetime.now)
    parent: Optional[uuid.UUID]
    children: list[uuid.UUID]
    content: str  # rev: mapping[id].message.content.parts[0]; mapping[id].message.content.content_type 为 text
    rev_metadata: Optional[RevChatMessageMetadata]  # rev only
    api_metadata: Optional[ApiChatMessageMetadata]  # api only

    @classmethod
    def new(cls, role, content):
        return cls(
            id=uuid.uuid4(),
            role=role,
            create_time=datetime.datetime.now(),
            parent=None,
            children=[],
            content=content)


class ConversationHistoryDocument(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    type: Literal["rev", "api"]
    title: str
    create_time: datetime.datetime
    update_time: datetime.datetime
    mapping: dict[str, ChatMessage]
    current_node: uuid.UUID
    current_model: Optional[Union[ChatModel, str]]

    class Settings:
        name = "conversation_history"
