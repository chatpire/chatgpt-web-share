import datetime
import uuid
from typing import Optional, Any, Literal, Union, Annotated, Dict

from beanie import Document
from pydantic import BaseModel, Field

from api.schema.openai_schemas import OpenAIChatResponseUsage


# metadata 相关

class RevChatMessageMetadataPlugin(BaseModel):
    http_response_status: Optional[int]
    namespace: Optional[str]
    plugin_id: Optional[str]
    type: Optional[str]


class RevChatMessageMetadataCiteData(BaseModel):
    title: Optional[str]
    url: Optional[str]
    text: Optional[str]


class RevChatMessageMetadataCite(BaseModel):
    citation_format: Optional[dict[str, Any]]
    metadata_list: Optional[list[RevChatMessageMetadataCiteData]]


class RevChatMessageMetadata(BaseModel):
    type: Literal["rev"] = Field(default="rev", const=True)
    # 以下只有assistant有
    # mapping[id].message.metadata 中的内容 加上 mapping[id].message 中的 weight, end_turn
    finish_details: Optional[dict[str, Any]]
    weight: Optional[float]
    end_turn: Optional[bool]
    message_status: Optional[str]
    recipient: Optional[Literal['all', 'browser'] | str]
    fallback_content: Optional[Any]  # 当解析content_type失败时，此字段存储原始的content
    # plugins 相关
    invoked_plugin: Optional[RevChatMessageMetadataPlugin]
    # browsing 相关
    command: Optional[Literal['search'] | str]
    args: Optional[list[str]]  # 例如：['May 17, 2023 stock market news']
    status: Optional[Literal['finished'] | str]
    cite_metadata: Optional[RevChatMessageMetadataCite] = Field(alias="_cite_metadata")  # _cite_metadata


class ApiChatMessageMetadata(BaseModel):
    type: Literal['api'] = Field(default="api", const=True)
    usage: Optional[OpenAIChatResponseUsage]
    finish_reason: Optional[str]


# content 相关


class RevChatMessageTextContent(BaseModel):
    content_type: Literal['text'] = Field(default="text", const=True)
    parts: Optional[list[str]]


class RevChatMessageCodeContent(BaseModel):
    content_type: Literal['code'] = Field(default="code", const=True)
    language: Optional[str]
    text: Optional[str]


class RevChatMessageTetherBrowsingDisplayContent(BaseModel):
    content_type: Literal['tether_browsing_display'] = Field(default="tether_browsing_display", const=True)
    result: Optional[str]


class RevChatMessageTetherQuoteContent(BaseModel):
    content_type: Literal['tether_quote'] = Field(default="tether_quote", const=True)
    url: Optional[str]
    domain: Optional[str]
    text: Optional[str]
    title: Optional[str]


RevChatMessageContent = Annotated[
    Union[
        RevChatMessageTextContent, RevChatMessageCodeContent, RevChatMessageTetherBrowsingDisplayContent,
        RevChatMessageTetherQuoteContent
    ], Field(discriminator='content_type')]


class ApiChatMessageTextContent(BaseModel):
    content_type: Literal['text'] = Field(default="text", const=True)
    text: str


# message

class BaseChatMessage(BaseModel):
    id: uuid.UUID
    type: Literal["rev", "api"]
    role: Literal['system', 'user', 'assistant', 'tool'] | str
    author_name: Optional[str]  # rev: mapping[id].message.author.name
    model: Optional[str]  # rev: mapping[id].message.metadata.model_slug -> ChatModel
    create_time: Optional[datetime.datetime]
    parent: Optional[uuid.UUID]
    children: list[uuid.UUID]
    content: Optional[RevChatMessageContent | ApiChatMessageTextContent | str]
    """
    关于 content:
    这里的 str 仅方便前端临时使用，实际上不可以直接存储 str
    """
    # metadata: Union[RevChatMessageMetadata, ApiChatMessageMetadata] = Field(discriminator='type')
    metadata: Optional[Annotated[Union[RevChatMessageMetadata, ApiChatMessageMetadata], Field(discriminator='type')]]


class RevChatMessage(BaseChatMessage):
    type: Literal["rev"] = Field(default="rev", const=True)
    content: Optional[RevChatMessageContent]


class ApiChatMessage(BaseChatMessage):
    type: Literal["api"] = Field(default="api", const=True)
    # content: Union[ApiChatMessageTextContent] = Field(..., discriminator='content_type')
    content: Optional[ApiChatMessageTextContent]


# history document


class RevConversationHistoryExtra(BaseModel):
    moderation_results: Optional[list[Any]]
    plugin_ids: Optional[list[str]]


class BaseConversationHistory(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    type: Literal["rev", "api"]
    title: str
    create_time: datetime.datetime
    update_time: datetime.datetime
    mapping: dict[str, BaseChatMessage]
    current_node: Optional[uuid.UUID]
    current_model: Optional[str]
    rev_extra: Optional[RevConversationHistoryExtra]

    class Settings:
        is_root = True


class RevConversationHistoryDocument(Document, BaseConversationHistory):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    type: Literal["rev"] = Field(default="rev", const=True)
    mapping: dict[str, RevChatMessage]

    class Settings:
        name = "rev_conversation_history"


class ApiConversationHistoryDocument(Document, BaseConversationHistory):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    type: Literal["api"] = Field(default="api", const=True)
    mapping: dict[str, ApiChatMessage]

    class Settings:
        name = "api_conversation_history"
