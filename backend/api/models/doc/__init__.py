import datetime
import uuid
from typing import Optional, Any, Literal, Union, Annotated, Dict

from beanie import Document, TimeSeriesConfig, Granularity
from pydantic import BaseModel, Field

from api.enums import OpenaiWebChatModels, OpenaiApiChatModels
from api.models.doc.openai_web_code_interpreter import OpenaiWebChatMessageMetadataAggregateResult, \
    OpenaiWebChatMessageMetadataAttachment
from api.models.types import SourceTypeLiteral
from api.schemas.openai_schemas import OpenaiChatResponseUsage
from api.conf import Config

config = Config()


# metadata 相关

class OpenaiWebChatMessageMetadataPlugin(BaseModel):
    http_response_status: Optional[int]
    namespace: Optional[str]
    plugin_id: Optional[str]
    type: Optional[str]


class OpenaiWebChatMessageMetadataCiteData(BaseModel):
    title: Optional[str]
    url: Optional[str]
    text: Optional[str]


class OpenaiWebChatMessageMetadataCite(BaseModel):
    citation_format: Optional[dict[str, Any]]
    metadata_list: Optional[list[OpenaiWebChatMessageMetadataCiteData]]


class OpenaiWebChatMessageMetadataCitation(BaseModel):
    start_ix: Optional[int]
    end_ix: Optional[int]
    metadata: Optional[OpenaiWebChatMessageMetadataCiteData]


class OpenaiWebChatMessageMetadataAggregateResultJupyterMessage(BaseModel):
    msg_type: Optional[Literal['status', 'execute_input', 'execute_result', 'error'] | str]
    parent_header: Optional[dict[str, Any]]
    content: Optional[dict[str, Any]]


class OpenaiWebChatMessageMetadata(BaseModel):
    source: Literal["openai_web"]
    # 以下只有assistant有
    # mapping[id].message.metadata 中的内容 加上 mapping[id].message 中的 weight, end_turn
    finish_details: Optional[dict[str, Any]]
    weight: Optional[float]
    end_turn: Optional[bool]
    message_status: Optional[str]
    recipient: Optional[Literal['all', 'browser', 'python'] | str]
    fallback_content: Optional[Any]  # 当解析content_type失败时，此字段存储原始的content
    # plugins 相关
    invoked_plugin: Optional[OpenaiWebChatMessageMetadataPlugin]
    # browsing 相关
    command: Optional[Literal['search'] | str]
    args: Optional[list[str]]  # 例如：['May 17, 2023 stock market news']
    status: Optional[Literal['finished'] | str]
    cite_metadata: Optional[OpenaiWebChatMessageMetadataCite] = Field(alias="_cite_metadata")  # _cite_metadata
    citations: Optional[list[OpenaiWebChatMessageMetadataCitation]]
    # code execution 相关
    attachments: Optional[list[OpenaiWebChatMessageMetadataAttachment]]
    is_complete: Optional[bool]
    aggregate_result: Optional[OpenaiWebChatMessageMetadataAggregateResult]


class OpenaiApiChatMessageMetadata(BaseModel):
    source: Literal['openai_api']
    usage: Optional[OpenaiChatResponseUsage]
    finish_reason: Optional[str]


# content 相关


class OpenaiWebChatMessageTextContent(BaseModel):
    content_type: Literal['text']
    parts: Optional[list[str]]


class OpenaiWebChatMessageMultimodalTextMetadataDalle(BaseModel):
    prompt: Optional[str]
    seed: Optional[int]
    serialization_title: Optional[str]


class OpenaiWebChatMessageMultimodalTextMetadata(BaseModel):
    dalle: Optional[OpenaiWebChatMessageMultimodalTextMetadataDalle]


class OpenaiWebChatMessageMultimodalTextContentImagePart(BaseModel):
    asset_pointer: Optional[str]
    size_bytes: Optional[int]
    width: Optional[int]
    height: Optional[int]
    metadata: Optional[OpenaiWebChatMessageMultimodalTextMetadata]


class OpenaiWebChatMessageMultimodalTextContent(BaseModel):
    content_type: Literal['multimodal_text']
    parts: Optional[list[str | OpenaiWebChatMessageMultimodalTextContentImagePart | Any]]


class OpenaiWebChatMessageCodeContent(BaseModel):
    content_type: Literal['code']
    language: Optional[str]
    text: Optional[str]


class OpenaiWebChatMessageExecutionOutputContent(BaseModel):
    content_type: Literal['execution_output']
    text: Optional[str]


class OpenaiWebChatMessageStderrContent(BaseModel):
    content_type: Literal['stderr']
    text: Optional[str]


class OpenaiWebChatMessageTetherBrowsingDisplayContent(BaseModel):
    content_type: Literal['tether_browsing_display']
    result: Optional[str]


class OpenaiWebChatMessageTetherQuoteContent(BaseModel):
    content_type: Literal['tether_quote']
    url: Optional[str]
    domain: Optional[str]
    text: Optional[str]
    title: Optional[str]


class OpenaiWebChatMessageSystemErrorContent(BaseModel):
    content_type: Literal['system_error']
    name: Optional[Literal['tool_error'] | str]
    text: Optional[str]


OpenaiWebChatMessageContent = Annotated[
    Union[
        OpenaiWebChatMessageTextContent,
        OpenaiWebChatMessageMultimodalTextContent,
        OpenaiWebChatMessageCodeContent,
        OpenaiWebChatMessageExecutionOutputContent,
        OpenaiWebChatMessageStderrContent,
        OpenaiWebChatMessageTetherBrowsingDisplayContent,
        OpenaiWebChatMessageTetherQuoteContent,
        OpenaiWebChatMessageSystemErrorContent
    ], Field(discriminator='content_type')]


class OpenaiApiChatMessageTextContent(BaseModel):
    content_type: Literal['text']
    text: str


# message

class BaseChatMessage(BaseModel):
    id: uuid.UUID
    source: SourceTypeLiteral
    role: Literal['system', 'user', 'assistant', 'tool'] | str
    author_name: Optional[Literal['browser', 'python'] | str]  # rev: mapping[id].message.author.name
    model: Optional[str]  # rev: mapping[id].message.metadata.model_slug -> ChatModel
    create_time: Optional[datetime.datetime]
    parent: Optional[uuid.UUID]
    children: list[uuid.UUID]
    content: Optional[OpenaiWebChatMessageContent | OpenaiApiChatMessageTextContent]
    metadata: Optional[
        Annotated[Union[OpenaiWebChatMessageMetadata, OpenaiApiChatMessageMetadata], Field(discriminator='source')]]


class OpenaiWebChatMessage(BaseChatMessage):
    source: Literal["openai_web"]
    content: Optional[OpenaiWebChatMessageContent]


class OpenaiApiChatMessage(BaseChatMessage):
    source: Literal["openai_api"]
    # content: Union[ApiChatMessageTextContent] = Field(..., discriminator='content_type')
    content: Optional[OpenaiApiChatMessageTextContent]


# history document


class OpenaiWebConversationHistoryMeta(BaseModel):
    source: Literal["openai_web"]
    moderation_results: Optional[list[Any]]
    plugin_ids: Optional[list[str]]


class OpenaiApiConversationHistoryMeta(BaseModel):
    source: Literal["openai_api"]


class BaseConversationHistory(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    source: SourceTypeLiteral
    title: str
    create_time: datetime.datetime
    update_time: datetime.datetime
    mapping: dict[str, BaseChatMessage]
    current_node: Optional[uuid.UUID]
    current_model: Optional[str]
    metadata: Optional[Annotated[
        Union[OpenaiWebConversationHistoryMeta, OpenaiApiConversationHistoryMeta], Field(discriminator='source')]]


class OpenaiWebConversationHistoryDocument(Document, BaseConversationHistory):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    source: Literal["openai_web"]
    mapping: dict[str, OpenaiWebChatMessage]
    metadata: Optional[OpenaiWebConversationHistoryMeta]

    class Settings:
        name = "openai_web_conversation_history"
        validate_on_save = True


class OpenaiApiConversationHistoryDocument(Document, BaseConversationHistory):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    source: Literal["openai_api"]
    mapping: dict[str, OpenaiApiChatMessage]

    class Settings:
        name = "openai_api_conversation_history"
        validate_on_save = True


class RequestLogMeta(BaseModel):
    route_path: str
    method: Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] | str


class RequestLogDocument(Document):
    time: datetime.datetime = Field(default_factory=lambda: datetime.datetime.utcnow())
    meta: RequestLogMeta
    user_id: Optional[int]
    elapsed_ms: float
    status: Optional[int]

    class Settings:
        name = "request_logs"
        timeseries = TimeSeriesConfig(
            time_field="time",
            meta_field="meta",
            granularity=Granularity.seconds,
            expire_after_seconds=config.stats.request_stats_ttl
        )


class OpenaiWebAskLogMeta(BaseModel):
    source: Literal['openai_web']
    model: OpenaiWebChatModels


class OpenaiApiAskLogMeta(BaseModel):
    source: Literal['openai_api']
    model: OpenaiApiChatModels


class AskLogDocument(Document):
    time: datetime.datetime = Field(default_factory=lambda: datetime.datetime.utcnow())
    meta: Union[OpenaiWebAskLogMeta, OpenaiApiAskLogMeta] = Field(discriminator='source')
    user_id: int
    queueing_time: Optional[float]
    ask_time: Optional[float]

    class Settings:
        name = "ask_logs"
        timeseries = TimeSeriesConfig(
            time_field="time",
            meta_field="meta",
            granularity=Granularity.seconds,
            expire_after_seconds=config.stats.ask_stats_ttl
        )
