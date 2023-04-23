import uuid
import datetime
from typing import List, Optional

from fastapi_users import schemas
from pydantic import Field, BaseModel, validator, EmailStr

from api.conf.config_model import ChatGPTSetting, Credentials
from api.enums import RevChatStatus, RevChatModels, ApiChatModels
from api.models.json_models import RevChatGPTAskLimits, RevChatGPTTimeLimits


class UserSettingSchema(BaseModel):
    id: int | None
    user_id: int | None
    can_use_revchatgpt: bool = True
    revchatgpt_available_models: list[str] = [RevChatModels.default.value, RevChatModels.gpt4.value]
    revchatgpt_ask_limits: RevChatGPTAskLimits = RevChatGPTAskLimits()
    revchatgpt_time_limits: RevChatGPTTimeLimits = RevChatGPTTimeLimits()
    can_use_openai_api: bool = True
    openai_api_credits: float = 0.0
    openai_api_available_models: list[str] = [ApiChatModels.gpt3]
    can_use_custom_openai_api: bool = True
    custom_openai_api_key: str | None

    @staticmethod
    def unlimited():
        return UserSettingSchema(
            can_use_revchatgpt=True,
            revchatgpt_available_models=[m.value for m in RevChatModels],
            revchatgpt_ask_limits=RevChatGPTAskLimits.unlimited(),
            revchatgpt_time_limits=RevChatGPTTimeLimits.unlimited(),
            can_use_openai_api=True,
            openai_api_credits=-1,
            openai_api_available_models=[m.value for m in ApiChatModels],
            can_use_custom_openai_api=True,
        )

    class Config:
        orm_mode = True


class UserRead(schemas.BaseUser[int]):
    id: int
    username: str
    nickname: str
    email: EmailStr
    rev_chat_status: RevChatStatus
    active_time: datetime.datetime | None
    created_time: datetime.datetime
    avatar: str | None
    is_superuser: bool
    is_active: bool
    is_verified: bool
    setting: "UserSettingSchema"


class UserReadAdmin(UserRead):
    remark: str | None


class UserUpdate(schemas.BaseUserUpdate):
    nickname: str | None
    email: str | None
    avatar: str | None


class UserUpdateAdmin(UserUpdate):
    username: str | None
    remark: str | None


class UserCreate(schemas.BaseUserCreate):
    username: str
    nickname: str
    email: EmailStr
    avatar: str | None
    remark: str | None
    setting: UserSettingSchema = UserSettingSchema()


class RevConversationSchema(BaseModel):
    id: int = -1
    conversation_id: uuid.UUID | None
    title: str | None
    user_id: int | None
    is_valid: bool | None
    model_name: RevChatModels | None
    created_time: datetime.datetime | None
    active_time: datetime.datetime | None

    class Config:
        use_enum_values = True
        orm_mode = True


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
