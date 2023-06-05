import datetime
from typing import Optional, Generic, TypeVar, get_args

from pydantic import BaseModel, Field, create_model, root_validator
from pydantic.generics import GenericModel

from api.enums import OpenaiWebChatModels, OpenaiApiChatModels

ModelT = TypeVar('ModelT', bound=OpenaiWebChatModels | OpenaiApiChatModels)


class RevPerModelAskCount(BaseModel):
    gpt_3_5: int = 0
    gpt_4: int = 0
    gpt_4_mobile: int = 0
    gpt_4_browsing: int = 0
    gpt_4_plugins: int = 0

    @root_validator(pre=True)
    def check(cls, values):
        # 如果某个值缺失，则默认设置为0
        for model in list(OpenaiWebChatModels):
            if model not in values:
                values[model] = 0
        return values

    @staticmethod
    def default():
        return RevPerModelAskCount(gpt_3_5=0, gpt_4=0, gpt_4_mobile=0, gpt_4_browsing=0, gpt_4_plugins=0)

    @staticmethod
    def unlimited():
        return RevPerModelAskCount(gpt_3_5=-1, gpt_4=-1, gpt_4_mobile=-1, gpt_4_browsing=-1, gpt_4_plugins=-1)


class ApiPerModelAskCount(BaseModel):
    gpt_3_5: int = 0
    gpt_4: int = 0

    @root_validator(pre=True)
    def check(cls, values):
        for model in list(OpenaiApiChatModels):
            if model not in values:
                values[model] = 0
        return values

    @staticmethod
    def default():
        return ApiPerModelAskCount(gpt_3_5=0, gpt_4=0)

    @staticmethod
    def unlimited():
        return ApiPerModelAskCount(gpt_3_5=-1, gpt_4=-1)


class TimeWindowRateLimit(BaseModel):
    window_seconds: int = Field(..., description="时间窗口大小，单位为秒")
    max_requests: int = Field(..., description="在给定时间窗口内最多的请求次数")


class DailyTimeSlot(BaseModel):
    start_time: datetime.time = Field(..., description="每天可使用的开始时间")
    end_time: datetime.time = Field(..., description="每天可使用的结束时间")


class CustomOpenaiApiSettings(BaseModel):
    url: Optional[str]
    key: Optional[str]
