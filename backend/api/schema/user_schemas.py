import datetime
from typing import TypeVar, Generic, Type, Optional

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr
from pydantic.generics import GenericModel

from api.enums import RevChatStatus, RevChatModels, ApiChatModels
from api.models.json import CustomOpenaiApiSettings, TimeWindowRateLimit, DailyTimeSlot, \
    RevPerModelAskCount, ApiPerModelAskCount

ModelT = TypeVar('ModelT', bound=RevChatModels | ApiChatModels)


class BaseSourceSettingSchema(BaseModel):
    allow_to_use: bool
    valid_until: Optional[datetime.datetime]  # None 表示永久有效
    max_conv_count: int
    total_ask_count: int
    rate_limits: list[TimeWindowRateLimit]
    daily_available_time_slots: list[DailyTimeSlot]

    @staticmethod
    def default():  # TODO: 从配置文件读取
        return BaseSourceSettingSchema(
            allow_to_use=True,
            valid_until=None,
            max_conv_count=10,
            total_ask_count=0,
            rate_limits=[],
            daily_available_time_slots=[DailyTimeSlot(start_time=datetime.time(0, 0, 0),
                                                      end_time=datetime.time(23, 59, 59))]
        )

    @staticmethod
    def unlimited():
        return BaseSourceSettingSchema(
            allow_to_use=True,
            valid_until=None,
            max_conv_count=-1,
            total_ask_count=-1,
            rate_limits=[],
            daily_available_time_slots=[DailyTimeSlot(start_time=datetime.time(0, 0, 0),
                                                      end_time=datetime.time(23, 59, 59))]
        )


class RevSourceSettingSchema(BaseSourceSettingSchema):
    available_models: list[RevChatModels]
    per_model_ask_count: RevPerModelAskCount

    @staticmethod
    def default():
        return RevSourceSettingSchema(
            available_models=[RevChatModels(m) for m in RevChatModels],
            per_model_ask_count=RevPerModelAskCount.default(),
            **BaseSourceSettingSchema.default().dict()
        )

    @staticmethod
    def unlimited():
        return RevSourceSettingSchema(
            available_models=[RevChatModels(m) for m in RevChatModels],
            per_model_ask_count=RevPerModelAskCount.unlimited(),
            **BaseSourceSettingSchema.unlimited().dict()
        )

    class Config:
        orm_mode = True


class ApiSourceSettingSchema(BaseSourceSettingSchema):
    available_models: list[ApiChatModels]
    per_model_ask_count: ApiPerModelAskCount
    allow_custom_openai_api: bool
    custom_openai_api_settings: CustomOpenaiApiSettings

    @staticmethod
    def default():
        return ApiSourceSettingSchema(
            available_models=[ApiChatModels(m) for m in ApiChatModels],
            per_model_ask_count=ApiPerModelAskCount.default(),
            **BaseSourceSettingSchema.default().dict(),
            allow_custom_openai_api=False,
            custom_openai_api_settings=CustomOpenaiApiSettings()
        )

    @staticmethod
    def unlimited():
        return ApiSourceSettingSchema(
            available_models=[ApiChatModels(m) for m in ApiChatModels],
            per_model_ask_count=ApiPerModelAskCount.unlimited(),
            **BaseSourceSettingSchema.unlimited().dict(),
            allow_custom_openai_api=True,
            custom_openai_api_settings=CustomOpenaiApiSettings()
        )

    class Config:
        orm_mode = True


class UserSettingSchema(BaseModel):
    id: int | None
    user_id: int | None
    credits: float
    rev: RevSourceSettingSchema
    api: ApiSourceSettingSchema

    @staticmethod
    def default():
        return UserSettingSchema(
            credits=0,
            rev=RevSourceSettingSchema.default(),
            api=ApiSourceSettingSchema.default()
        )

    @staticmethod
    def unlimited():
        return UserSettingSchema(
            credits=-1,
            rev=RevSourceSettingSchema.unlimited(),
            api=ApiSourceSettingSchema.unlimited()
        )

    class Config:
        orm_mode = True


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
    setting: UserSettingSchema


class UserReadAdmin(UserRead):
    remark: str | None


class UserUpdate(schemas.BaseUserUpdate):
    nickname: str | None
    email: str | None
    avatar: str | None


class UserUpdateAdmin(UserUpdate):
    username: str | None
    remark: str | None
