import datetime
import uuid
from typing import Any

from fastapi_users import schemas
from pydantic import BaseModel, validator, EmailStr
from pydantic.utils import GetterDict

from api.conf.config_model import ChatGPTSetting, Credentials
from api.enums import RevChatStatus, RevChatModels, ApiChatModels
from api.models.json_models import RevChatAskLimits, RevChatTimeLimits


class UserSettingGetterDict(GetterDict):
    def get(self, key: Any, default: Any = None) -> Any:
        if key == "revchatgpt_available_models":
            if getattr(self._obj, key):
                return [RevChatModels(m) for m in getattr(self._obj, key) if m in RevChatModels.values()]
            else:
                return []
        elif key == "openai_api_available_models":
            if getattr(self._obj, key):
                return [ApiChatModels(m) for m in getattr(self._obj, key) if m in ApiChatModels.values()]
            else:
                return []
        return super().get(key, default)


class UserSettingSchema(BaseModel):
    id: int | None
    user_id: int | None
    can_use_revchatgpt: bool
    revchatgpt_available_models: list[RevChatModels]
    revchatgpt_ask_limits: RevChatAskLimits
    revchatgpt_time_limits: RevChatTimeLimits
    can_use_openai_api: bool
    openai_api_credits: float
    openai_api_available_models: list[ApiChatModels]
    can_use_custom_openai_api: bool
    custom_openai_api_key: str | None

    @staticmethod
    def default():
        return UserSettingSchema(
            can_use_revchatgpt=True,
            revchatgpt_available_models=[RevChatModels.default, RevChatModels.gpt4],
            revchatgpt_ask_limits=RevChatAskLimits.default(),
            revchatgpt_time_limits=RevChatTimeLimits.default(),
            can_use_openai_api=True,
            openai_api_credits=0.0,
            openai_api_available_models=[m.value for m in ApiChatModels],
            can_use_custom_openai_api=True,
            custom_openai_api_key=None,
        )

    @staticmethod
    def unlimited():
        return UserSettingSchema(
            can_use_revchatgpt=True,
            revchatgpt_available_models=[m for m in RevChatModels],
            revchatgpt_ask_limits=RevChatAskLimits.unlimited(),
            revchatgpt_time_limits=RevChatTimeLimits.unlimited(),
            can_use_openai_api=True,
            openai_api_credits=-1,
            openai_api_available_models=[m for m in ApiChatModels],
            can_use_custom_openai_api=True,
            custom_openai_api_key=None
        )

    class Config:
        orm_mode = True
        getter_dict = UserSettingGetterDict


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
    setting: UserSettingSchema = UserSettingSchema.default()


class RevConversationSchema(BaseModel):
    id: int = -1
    conversation_id: uuid.UUID | None
    title: str | None
    user_id: int | None
    is_valid: bool = True
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
