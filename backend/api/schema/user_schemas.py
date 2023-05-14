import datetime
from typing import TypeVar, Generic, Type, Optional

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr
from pydantic.generics import GenericModel

from api.enums import RevChatStatus, RevChatModels, ApiChatModels
from api.models.json import CustomOpenaiApiSettings, TimeWindowRateLimit, DailyTimeSlot

ModelT = TypeVar('ModelT', bound=RevChatModels | ApiChatModels)


class SourceSettingSchema(GenericModel, Generic[ModelT]):
    allow_to_use: bool
    valid_until: Optional[datetime.datetime]  # None 表示永久有效
    available_models: list[ModelT]
    max_conv_count: int
    total_ask_count: int
    per_model_ask_count: dict[ModelT, int]  # 除非明确指定-1（无限制），不存在的模型默认为0
    rate_limits: list[TimeWindowRateLimit]
    daily_available_time_slots: list[DailyTimeSlot]
    api_credits: float
    allow_custom_openai_api: bool
    custom_openai_api_settings: CustomOpenaiApiSettings

    @staticmethod
    def default(model_cls: Type[ModelT]):  # TODO: 从配置文件读取
        return SourceSettingSchema(
            allow_to_use=True,
            valid_until=None,
            available_models=list(model_cls),
            max_conv_count=10,
            total_ask_count=0,
            per_model_ask_count={model: 0 for model in model_cls},
            rate_limits=[],
            daily_available_time_slots=[DailyTimeSlot(start_time=datetime.time(0, 0, 0),
                                                      end_time=datetime.time(23, 59, 59))],
            api_credits=0,
            allow_custom_openai_api=False,
            custom_openai_api_settings=CustomOpenaiApiSettings(url=None, key=None)
        )

    @staticmethod
    def unlimited(model_cls: Type[ModelT]):
        return SourceSettingSchema(
            allow_to_use=True,
            valid_until=None,
            available_models=list(model_cls),
            max_conv_count=-1,
            total_ask_count=-1,
            per_model_ask_count={model: -1 for model in model_cls},
            rate_limits=[],
            daily_available_time_slots=[DailyTimeSlot(start_time=datetime.time(0, 0, 0),
                                                      end_time=datetime.time(23, 59, 59))],
            api_credits=-1,
            allow_custom_openai_api=False,
            custom_openai_api_settings=CustomOpenaiApiSettings(url=None, key=None)
        )

    class Config:
        orm_mode = True
        # getter_dict = UserSettingGetterDict


class UserSettingSchema(BaseModel):
    id: int | None
    user_id: int | None

    rev: SourceSettingSchema[RevChatModels]
    api: SourceSettingSchema[ApiChatModels]

    @staticmethod
    def default():
        return UserSettingSchema(
            rev=SourceSettingSchema.default(RevChatModels),
            api=SourceSettingSchema.default(ApiChatModels)
        )

    @staticmethod
    def unlimited():
        return UserSettingSchema(
            rev=SourceSettingSchema.unlimited(RevChatModels),
            api=SourceSettingSchema.unlimited(ApiChatModels)
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
