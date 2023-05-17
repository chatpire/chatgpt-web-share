import datetime
import uuid
from typing import Optional, Any, Literal

from beanie import Document
from pydantic import BaseModel, Field

from api.schema.openai_schemas import OpenAIChatResponseUsage


class RevChatMessageMetadataPlugin(BaseModel):
    http_response_status: Optional[int]
    namespace: Optional[str]
    plugin_id: Optional[str]
    type: Optional[str]


class RevChatMessageMetadata(BaseModel):
    # mapping[id].message.metadata 中的内容 加上 mapping[id].message 中的 weight, end_turn
    # 以下只有assistant有
    finish_details: Optional[dict[str, Any]]
    weight: Optional[float]
    end_turn: Optional[bool]
    status: Optional[str]
    recipient: Optional[Literal['all'] | str]
    invoked_plugin: Optional[RevChatMessageMetadataPlugin]


class ApiChatMessageMetadata(BaseModel):
    usage: Optional[OpenAIChatResponseUsage]
    finish_reason: Optional[str]


class ChatMessage(BaseModel):
    id: uuid.UUID
    role: str  # rev: mapping[id].message.author.role: system, user, assistant
    model: Optional[str]  # rev: mapping[id].message.metadata.model_slug -> ChatModel
    create_time: Optional[datetime.datetime]
    parent: Optional[uuid.UUID]
    children: list[uuid.UUID]
    content: str  # rev: mapping[id].message.content.parts[0]; mapping[id].message.content.content_type 为 text
    content_type: Optional[str]
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


class RevConversationHistoryExtra(BaseModel):
    moderation_results: list[Any]
    plugin_ids: list[str]


class ConversationHistoryDocument(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    type: Literal["rev", "api"]
    title: str
    create_time: datetime.datetime
    update_time: datetime.datetime
    mapping: dict[str, ChatMessage]
    current_node: Optional[uuid.UUID]
    current_model: Optional[str]
    rev_extra: Optional[RevConversationHistoryExtra]

    class Settings:
        name = "conversation_history"
