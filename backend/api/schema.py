import uuid
import datetime
from typing import List

from fastapi_users import schemas
from pydantic import Field, BaseModel, validator

from api.conf.config_model import ChatGPTSetting, Credentials
from api.enums import ChatStatus, ChatModels


class UserRead(schemas.BaseUser[int]):
    id: int
    username: str
    nickname: str
    email: str
    active_time: datetime.datetime | None

    chat_status: ChatStatus

    can_use_paid: bool
    can_use_gpt4: bool
    max_conv_count: int | None
    available_ask_count: int | None
    available_gpt4_ask_count: int | None

    is_superuser: bool
    is_active: bool
    is_verified: bool


class LimitSchema(BaseModel):
    can_use_paid: bool | None = None
    can_use_gpt4: bool | None = None
    max_conv_count: int | None = None
    available_ask_count: int | None = None
    available_gpt4_ask_count: int | None = None


class UserUpdate(schemas.BaseUser[int]):
    nickname: str
    email: str = None


class UserCreate(schemas.BaseUserCreate):
    username: str
    email: str
    nickname: str
    can_use_paid: bool = False
    max_conv_count: int = -1
    available_ask_count: int = -1

    class Config:
        orm_mode = True


class ConversationSchema(BaseModel):
    id: int = -1
    conversation_id: uuid.UUID = None
    title: str = None
    user_id: int = None
    is_valid: bool = None
    model_name: ChatModels = None
    create_time: datetime.datetime = None
    active_time: datetime.datetime = None

    class Config:
        use_enum_values = True


class ServerStatusSchema(BaseModel):
    active_user_in_5m: int = None
    active_user_in_1h: int = None
    active_user_in_1d: int = None
    is_chatbot_busy: bool = None
    chatbot_waiting_count: int = None


class RequestStatistics(BaseModel):
    request_counts_interval: int
    request_counts: dict[int, list]  # {timestage: [count, [user_ids]]}
    ask_records: list  # list of (ask, time_used), timestamp.


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


class ConfigRead(BaseModel):
    chatgpt: ChatGPTSetting
    credentials_exist: dict[str, bool]


class ConfigUpdate(BaseModel):
    chatgpt: ChatGPTSetting
    credentials: Credentials
