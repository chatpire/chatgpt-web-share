from datetime import datetime, timezone
from typing import Optional, Union, Annotated

from pydantic import BaseModel, validator, Field

from api.models.doc import OpenaiWebAskLogMeta, OpenaiApiAskLogMeta


class SystemInfo(BaseModel):
    startup_time: float
    total_user_count: int
    total_conversation_count: int
    valid_conversation_count: int


class LogFilterOptions(BaseModel):
    max_lines: int = 100
    exclude_keywords: list[str] = None

    @validator("max_lines")
    def max_lines_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("max_lines must be positive")
        return v


datetime.now().astimezone()


class RequestLogAggregationID(BaseModel):
    start_time: Optional[datetime]
    route_path: Optional[str]
    method: Optional[str]


class RequestLogAggregation(BaseModel):
    id: RequestLogAggregationID = Field(alias="_id")  # 起始时间
    count: int  # 时间间隔内的请求数量
    user_ids: list[Optional[int]] = None  # 用户ID列表
    avg_elapsed_ms: Optional[float]

    class Config:
        json_encoders = {
            datetime: lambda d: d.astimezone(tz=timezone.utc)
        }


class AskLogAggregationID(BaseModel):
    start_time: datetime
    # meta: Union[OpenaiWebAskLogMeta, OpenaiApiAskLogMeta] = Field(discriminator='source')
    meta: Optional[Annotated[Union[OpenaiWebAskLogMeta, OpenaiApiAskLogMeta], Field(discriminator='source')]] = None


class AskLogAggregation(BaseModel):
    id: Optional[AskLogAggregationID] = Field(alias="_id")  # 起始时间
    count: int  # 时间间隔内的请求数量
    user_ids: list[Optional[int]] = None  # 用户ID列表
    total_queueing_time: Optional[float]
    total_ask_time: Optional[float]

    class Config:
        json_encoders = {
            datetime: lambda d: d.astimezone(tz=timezone.utc)
        }
