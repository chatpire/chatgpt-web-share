from datetime import datetime, timezone
from typing import Optional, Union, Annotated

from pydantic import field_validator, ConfigDict, BaseModel, Field, field_serializer

from api.models.doc import OpenaiWebAskLogMeta, OpenaiApiAskLogMeta


class SystemInfo(BaseModel):
    startup_time: float
    total_user_count: int
    total_conversation_count: int
    valid_conversation_count: int


class LogFilterOptions(BaseModel):
    max_lines: int = 100
    exclude_keywords: list[str] = None

    @field_validator("max_lines")
    @classmethod
    def max_lines_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("max_lines must be positive")
        return v


class RequestLogAggregationID(BaseModel):
    start_time: Optional[datetime] = None
    route_path: Optional[str] = None
    method: Optional[str] = None

    @field_serializer("start_time")
    def serialize_dt(self, start_time: Optional[datetime], _info):
        if start_time:
            return start_time.replace(tzinfo=timezone.utc)
        return None


class RequestLogAggregation(BaseModel):
    id: RequestLogAggregationID = Field(alias="_id")  # 起始时间
    count: int  # 时间间隔内的请求数量
    user_ids: list[Optional[int]] = None  # 用户ID列表
    avg_elapsed_ms: Optional[float] = None


class AskLogAggregationID(BaseModel):
    start_time: datetime
    # meta: Union[OpenaiWebAskLogMeta, OpenaiApiAskLogMeta] = Field(discriminator='source')
    meta: Optional[Annotated[Union[OpenaiWebAskLogMeta, OpenaiApiAskLogMeta], Field(discriminator='source')]] = None


class AskLogAggregation(BaseModel):
    id: Optional[AskLogAggregationID] = Field(None, alias="_id")  # 起始时间
    count: int  # 时间间隔内的请求数量
    user_ids: list[Optional[int]] = None  # 用户ID列表
    total_queueing_time: Optional[float] = None
    total_ask_time: Optional[float] = None
