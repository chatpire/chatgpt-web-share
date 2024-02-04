import datetime
import uuid
from typing import Optional, Any, Literal, Union, Annotated, Dict

from beanie import Document, TimeSeriesConfig, Granularity
from pydantic import BaseModel, Field, field_serializer

from api.enums import OpenaiWebChatModels, OpenaiApiChatModels
from api.models.doc.openai_web_code_interpreter import OpenaiWebChatMessageMetadataAggregateResult, \
    OpenaiWebChatMessageMetadataAttachment
from api.models.types import SourceTypeLiteral
from api.schemas.openai_schemas import OpenaiChatResponseUsage
from api.conf import Config

config = Config()


# metadata 相关


class OpenaiWebChatMessageMetadataFinishDetails(BaseModel):
    type: Optional[Literal['stop'] | str] = None
    stop_tokens: Optional[list[int]] = None


class OpenaiWebChatMessageMetadataPlugin(BaseModel):
    http_response_status: Optional[int] = None
    namespace: Optional[str] = None
    plugin_id: Optional[str] = None
    type: Optional[str] = None


class OpenaiWebChatMessageMetadataCiteData(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None


class OpenaiWebChatMessageMetadataCite(BaseModel):
    citation_format: Optional[dict[str, Any]] = None
    metadata_list: Optional[list[OpenaiWebChatMessageMetadataCiteData]] = None


class OpenaiWebChatMessageMetadataCitation(BaseModel):
    start_ix: Optional[int] = None
    end_ix: Optional[int] = None
    metadata: Optional[OpenaiWebChatMessageMetadataCiteData] = None


class OpenaiWebChatMessageMetadataAggregateResultJupyterMessage(BaseModel):
    msg_type: Optional[Literal['status', 'execute_input', 'execute_result', 'error'] | str] = None
    parent_header: Optional[dict[str, Any]] = None
    content: Optional[dict[str, Any]] = None


class OpenaiWebChatMessageMetadata(BaseModel):
    source: Literal["openai_web"]
    # 以下只有assistant有
    # mapping[id].message.metadata 中的内容 加上 mapping[id].message 中的 weight, end_turn
    finish_details: Optional[dict[str, Any]] = None
    weight: Optional[float] = None
    end_turn: Optional[bool] = None
    message_status: Optional[str] = None
    recipient: Optional[Literal['all', 'browser', 'python'] | str] = None
    fallback_content: Optional[Any] = None  # 当解析content_type失败时，此字段存储原始的content
    # plugins 相关
    invoked_plugin: Optional[OpenaiWebChatMessageMetadataPlugin] = None
    # browsing 相关
    command: Optional[Literal['search'] | str] = None
    args: Optional[list[Any]] = None  # 例如：['May 17, 2023 stock market news']
    cite_metadata: Optional[OpenaiWebChatMessageMetadataCite] = Field(None, alias="_cite_metadata")  # _cite_metadata
    citations: Optional[list[OpenaiWebChatMessageMetadataCitation]] = None
    # code execution 相关
    attachments: Optional[list[OpenaiWebChatMessageMetadataAttachment]] = None
    status: Optional[Literal['finished_successfully'] | str] = None
    is_complete: Optional[bool] = None
    aggregate_result: Optional[OpenaiWebChatMessageMetadataAggregateResult] = None

    timestamp_: Optional[datetime.datetime | str] = None


class OpenaiApiChatMessageMetadata(BaseModel):
    source: Literal['openai_api']
    usage: Optional[OpenaiChatResponseUsage] = None
    finish_reason: Optional[str] = None


# content 相关


class OpenaiWebChatMessageTextContent(BaseModel):
    content_type: Literal['text']
    parts: Optional[list[str]] = None


class OpenaiWebChatMessageMultimodalTextMetadataDalle(BaseModel):
    prompt: Optional[str] = None
    seed: Optional[int] = None
    serialization_title: Optional[str] = None


class OpenaiWebChatMessageMultimodalTextMetadata(BaseModel):
    dalle: Optional[OpenaiWebChatMessageMultimodalTextMetadataDalle] = None


class OpenaiWebChatMessageMultimodalTextContentImagePart(BaseModel):
    asset_pointer: Optional[str] = None
    size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    metadata: Optional[OpenaiWebChatMessageMultimodalTextMetadata] = None


class OpenaiWebChatMessageMultimodalTextContent(BaseModel):
    content_type: Literal['multimodal_text']
    parts: Optional[list[str | OpenaiWebChatMessageMultimodalTextContentImagePart | Any]] = None


class OpenaiWebChatMessageCodeContent(BaseModel):
    content_type: Literal['code']
    language: Optional[str] = None
    text: Optional[str] = None


class OpenaiWebChatMessageExecutionOutputContent(BaseModel):
    content_type: Literal['execution_output']
    text: Optional[str] = None


class OpenaiWebChatMessageStderrContent(BaseModel):
    content_type: Literal['stderr']
    text: Optional[str] = None


class OpenaiWebChatMessageTetherBrowsingDisplayContent(BaseModel):
    content_type: Literal['tether_browsing_display']
    result: Optional[str] = None


class OpenaiWebChatMessageTetherQuoteContent(BaseModel):
    content_type: Literal['tether_quote']
    url: Optional[str] = None
    domain: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None


class OpenaiWebChatMessageSystemErrorContent(BaseModel):
    content_type: Literal['system_error']
    name: Optional[Literal['tool_error'] | str] = None
    text: Optional[str] = None


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
    author_name: Optional[Literal['browser', 'python'] | str] = None  # rev: mapping[id].message.author.name
    model: Optional[str] = None  # rev: mapping[id].message.metadata.model_slug -> ChatModel
    create_time: Optional[datetime.datetime] = None
    parent: Optional[uuid.UUID] = None
    children: list[uuid.UUID]
    content: Optional[OpenaiWebChatMessageContent | OpenaiApiChatMessageTextContent] = None
    metadata: Optional[
        Annotated[
            Union[OpenaiWebChatMessageMetadata, OpenaiApiChatMessageMetadata], Field(discriminator='source')]] = None


class OpenaiWebChatMessage(BaseChatMessage):
    source: Literal["openai_web"]
    content: Optional[OpenaiWebChatMessageContent] = None


class OpenaiApiChatMessage(BaseChatMessage):
    source: Literal["openai_api"]
    # content: Union[ApiChatMessageTextContent] = Field(..., discriminator='content_type')
    content: Optional[OpenaiApiChatMessageTextContent] = None


# history document


class OpenaiWebConversationHistoryMeta(BaseModel):
    source: Literal["openai_web"]
    moderation_results: Optional[list[Any]] = None
    plugin_ids: Optional[list[str]] = None
    gizmo_id: Optional[str] = None
    is_archived: Optional[bool] = None
    conversation_template_id: Optional[str] = None


class OpenaiApiConversationHistoryMeta(BaseModel):
    source: Literal["openai_api"]


class BaseConversationHistory(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    source: SourceTypeLiteral
    title: str
    create_time: datetime.datetime
    update_time: datetime.datetime
    mapping: dict[str, BaseChatMessage]
    current_node: uuid.UUID
    current_model: Optional[str] = None
    metadata: Optional[Annotated[
        Union[OpenaiWebConversationHistoryMeta, OpenaiApiConversationHistoryMeta], Field(
            discriminator='source')]] = None


class OpenaiWebConversationHistoryDocument(Document, BaseConversationHistory):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    source: Literal["openai_web"]
    mapping: dict[str, OpenaiWebChatMessage]
    metadata: Optional[OpenaiWebConversationHistoryMeta] = None

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
    conversation_id: Optional[uuid.UUID] = None
    queueing_time: Optional[float]
    ask_time: Optional[float]

    @field_serializer("time")
    def serialize_dt(self, time: Optional[datetime.datetime], _info):
        if time:
            return time.replace(tzinfo=datetime.timezone.utc)
        return None

    class Settings:
        name = "ask_logs"
        timeseries = TimeSeriesConfig(
            time_field="time",
            meta_field="meta",
            granularity=Granularity.seconds,
            expire_after_seconds=config.stats.ask_stats_ttl
        )
