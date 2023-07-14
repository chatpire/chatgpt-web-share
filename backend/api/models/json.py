import datetime
from typing import Optional, Generic, TypeVar, get_args

from pydantic import BaseModel, Field, create_model, root_validator
from pydantic.generics import GenericModel

from api.enums import OpenaiWebChatModels, OpenaiApiChatModels

ModelT = TypeVar('ModelT', bound=OpenaiWebChatModels | OpenaiApiChatModels)


class OpenaiWebPerModelAskCount(BaseModel):
    __root__: dict[str, int] = {model: 0 for model in list(OpenaiWebChatModels)}

    @root_validator(pre=True)
    def check(cls, values):
        # 如果某个值缺失，则默认设置为0
        for model in list(OpenaiWebChatModels):
            if model not in values:
                values[model] = 0
        return values

    @staticmethod
    def unlimited():
        return OpenaiWebPerModelAskCount(__root__={model: -1 for model in list(OpenaiWebChatModels)})


class OpenaiApiPerModelAskCount(BaseModel):
    __root__: dict[str, int] = {model: 0 for model in list(OpenaiApiChatModels)}

    @root_validator(pre=True)
    def check(cls, values):
        for model in list(OpenaiApiChatModels):
            if model not in values:
                values[model] = 0
        return values

    @staticmethod
    def unlimited():
        return OpenaiApiPerModelAskCount(__root__={model: -1 for model in list(OpenaiApiChatModels)})


class TimeWindowRateLimit(BaseModel):
    window_seconds: int = Field(..., description="时间窗口大小，单位为秒")
    max_requests: int = Field(..., description="在给定时间窗口内最多的请求次数")


class DailyTimeSlot(BaseModel):
    start_time: datetime.time = Field(..., description="每天可使用的开始时间")
    end_time: datetime.time = Field(..., description="每天可使用的结束时间")


class CustomOpenaiApiSettings(BaseModel):
    url: Optional[str]
    key: Optional[str]
