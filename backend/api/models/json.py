import datetime
from typing import Optional, Generic, TypeVar, get_args, Literal

from pydantic import model_validator, BaseModel, Field, create_model, RootModel
from pydantic.generics import GenericModel

from api.enums import OpenaiWebChatModels, OpenaiApiChatModels

ModelT = TypeVar('ModelT', bound=OpenaiWebChatModels | OpenaiApiChatModels)


class OpenaiWebPerModelAskCount(RootModel[dict[str, int]]):
    root: dict[str, int] = {model: 0 for model in list(OpenaiWebChatModels)}

    @model_validator(mode="after")
    @classmethod
    def check(cls, m):
        # 如果某个值缺失，则默认设置为0
        for model in list(OpenaiWebChatModels):
            if model not in m.root:
                m.root[model] = 0
        return m

    @staticmethod
    def unlimited():
        return OpenaiWebPerModelAskCount(root={model: -1 for model in list(OpenaiWebChatModels)})


class OpenaiApiPerModelAskCount(RootModel[dict[str, int]]):
    root: dict[str, int] = {model: 0 for model in list(OpenaiApiChatModels)}

    @model_validator(mode="after")
    @classmethod
    def check(cls, m):
        for model in list(OpenaiApiChatModels):
            if model not in m.root:
                m.root[model] = 0
        return m

    @staticmethod
    def unlimited():
        return OpenaiApiPerModelAskCount(root={model: -1 for model in list(OpenaiApiChatModels)})


class TimeWindowRateLimit(BaseModel):
    window_seconds: int = Field(..., description="时间窗口大小，单位为秒")
    max_requests: int = Field(..., description="在给定时间窗口内最多的请求次数")


class DailyTimeSlot(BaseModel):
    start_time: datetime.time = Field(..., description="每天可使用的开始时间")
    end_time: datetime.time = Field(..., description="每天可使用的结束时间")


class CustomOpenaiApiSettings(BaseModel):
    url: Optional[str] = None
    key: Optional[str] = None


class UploadedFileOpenaiWebInfo(BaseModel):
    file_id: Optional[str] = None
    use_case: Optional[Literal['my_files', 'multimodal'] | str] = None
    upload_url: Optional[str] = Field(None, description="上传文件的url, 上传后应清空该字段")
    download_url: Optional[str] = None


class UploadedFileExtraInfo(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
