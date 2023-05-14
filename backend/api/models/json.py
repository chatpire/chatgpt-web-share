import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TimeWindowRateLimit(BaseModel):
    window_seconds: int = Field(..., description="时间窗口大小，单位为秒")
    max_requests: int = Field(..., description="在给定时间窗口内最多的请求次数")


class DailyTimeSlot(BaseModel):
    start_time: datetime.time = Field(..., description="每天可使用的开始时间")
    end_time: datetime.time = Field(..., description="每天可使用的结束时间")


class CustomOpenaiApiSettings(BaseModel):
    url: Optional[str]
    key: Optional[str]
