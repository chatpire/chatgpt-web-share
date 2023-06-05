import datetime
from typing import Optional

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr

from api.enums import OpenaiWebChatStatus, OpenaiWebChatModels, OpenaiApiChatModels
from api.models.json import CustomOpenaiApiSettings, TimeWindowRateLimit, DailyTimeSlot, \
    RevPerModelAskCount, ApiPerModelAskCount


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
            total_ask_count=-1,
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


class OpenaiWebSourceSettingSchema(BaseSourceSettingSchema):
    available_models: list[OpenaiWebChatModels]
    per_model_ask_count: RevPerModelAskCount

    @staticmethod
    def default():
        return OpenaiWebSourceSettingSchema(
            available_models=[OpenaiWebChatModels(m) for m in OpenaiWebChatModels],
            per_model_ask_count=RevPerModelAskCount.default(),
            **BaseSourceSettingSchema.default().dict()
        )

    @staticmethod
    def unlimited():
        return OpenaiWebSourceSettingSchema(
            available_models=[OpenaiWebChatModels(m) for m in OpenaiWebChatModels],
            per_model_ask_count=RevPerModelAskCount.unlimited(),
            **BaseSourceSettingSchema.unlimited().dict()
        )

    class Config:
        orm_mode = True


class OpenaiApiSourceSettingSchema(BaseSourceSettingSchema):
    available_models: list[OpenaiApiChatModels]
    per_model_ask_count: ApiPerModelAskCount
    allow_custom_openai_api: bool
    custom_openai_api_settings: CustomOpenaiApiSettings

    @staticmethod
    def default():
        return OpenaiApiSourceSettingSchema(
            available_models=[OpenaiApiChatModels(m) for m in OpenaiApiChatModels],
            per_model_ask_count=ApiPerModelAskCount.default(),
            **BaseSourceSettingSchema.default().dict(),
            allow_custom_openai_api=False,
            custom_openai_api_settings=CustomOpenaiApiSettings()
        )

    @staticmethod
    def unlimited():
        return OpenaiApiSourceSettingSchema(
            available_models=[OpenaiApiChatModels(m) for m in OpenaiApiChatModels],
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
    openai_web_chat_status: OpenaiWebChatStatus
    openai_web: OpenaiWebSourceSettingSchema
    openai_api: OpenaiApiSourceSettingSchema

    @staticmethod
    def default():
        return UserSettingSchema(
            credits=0,
            openai_web_chat_status=OpenaiWebChatStatus.idling,
            openai_web=OpenaiWebSourceSettingSchema.default(),
            openai_api=OpenaiApiSourceSettingSchema.default()
        )

    @staticmethod
    def unlimited():
        return UserSettingSchema(
            credits=-1,
            openai_web_chat_status=OpenaiWebChatStatus.idling,
            openai_web=OpenaiWebSourceSettingSchema.unlimited(),
            openai_api=OpenaiApiSourceSettingSchema.unlimited()
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
