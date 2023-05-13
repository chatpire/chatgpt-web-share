import datetime
from typing import TypeVar

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, Field

from api.enums import RevChatStatus, ChatModel
from api.models import ChatTypeDict
from api.models.json_models import AskLimitSetting, AskTimeLimits


class UserSettingSchema(BaseModel):
    id: int | None
    user_id: int | None
    allow_chat_type: ChatTypeDict[bool]
    available_models: ChatTypeDict[list[ChatModel]]
    ask_count_limits: ChatTypeDict[AskLimitSetting]
    ask_time_limits: ChatTypeDict[AskTimeLimits]
    api_credits: float = Field(default=0.0, description="Credits for OpenAI API, not support unlimited (-1)")
    allow_custom_openai_api: bool
    custom_openai_api_url: str | None
    custom_openai_api_key: str | None

    @staticmethod
    def default():
        return UserSettingSchema(
            allow_chat_type=ChatTypeDict[bool](rev=True, api=True),
            available_models=ChatTypeDict[list[ChatModel]](rev=[ChatModel.gpt_3_5],
                                                           api=[ChatModel.gpt_3_5, ChatModel.gpt_4]),
            ask_count_limits=ChatTypeDict[AskLimitSetting](rev=AskLimitSetting.default(),
                                                           api=AskLimitSetting.default()),
            ask_time_limits=ChatTypeDict[AskTimeLimits](rev=AskTimeLimits.default(), api=AskTimeLimits.default()),
            api_credits=0.0,
            allow_custom_openai_api=True,
        )

    @staticmethod
    def unlimited():
        return UserSettingSchema(
            allow_chat_type=ChatTypeDict[bool](rev=True, api=True),
            available_models=ChatTypeDict[list[ChatModel]](rev=[ChatModel.gpt_3_5, ChatModel.gpt_4],
                                                           api=[ChatModel.gpt_3_5, ChatModel.gpt_4]),
            ask_count_limits=ChatTypeDict[AskLimitSetting](rev=AskLimitSetting.unlimited(),
                                                           api=AskLimitSetting.unlimited()),
            ask_time_limits=ChatTypeDict[AskTimeLimits](rev=AskTimeLimits.unlimited(),
                                                        api=AskTimeLimits.unlimited()),
            api_credits=-1,
            allow_custom_openai_api=True,
        )

    class Config:
        orm_mode = True
        # getter_dict = UserSettingGetterDict


class UserCreate(schemas.BaseUserCreate):
    username: str
    nickname: str
    email: EmailStr
    avatar: str | None
    remark: str | None
    # setting: UserSettingSchema = UserSettingSchema.default()


class UserRead(schemas.BaseUser[int]):
    id: int
    username: str
    nickname: str
    email: EmailStr
    rev_chat_status: RevChatStatus
    last_active_time: datetime.datetime | None
    create_time: datetime.datetime
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
