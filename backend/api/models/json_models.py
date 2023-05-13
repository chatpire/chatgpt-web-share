from typing import Optional, Generic, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

from api.enums import ChatModel, ChatSourceTypes

DataT = TypeVar('DataT')


class ChatTypeDict(GenericModel, Generic[DataT]):
    rev: DataT
    api: DataT

    def __getitem__(self, item: ChatSourceTypes | str):
        return getattr(self, item)


class ChatModelDict(GenericModel, Generic[DataT]):
    gpt_3_5: DataT
    gpt_4: DataT

    def __getitem__(self, item: ChatModel | str):
        return getattr(self, item)


class AskLimitSetting(BaseModel):
    max_conv_count: int
    total_ask_count: int
    per_model_ask_count: ChatModelDict[int] = Field(title="per_model_ask_count")

    @staticmethod
    def default():
        return AskLimitSetting(
            max_conv_count=1,
            total_ask_count=0,
            per_model_ask_count=ChatModelDict[int](gpt_3_5=0, gpt_4=0))

    @staticmethod
    def unlimited():
        return AskLimitSetting(
            max_conv_count=-1,
            total_ask_count=-1,
            per_model_ask_count=ChatModelDict[int](gpt_3_5=-1, gpt_4=-1))


class AskTimeLimits(BaseModel):
    # time_window_limits: dict[ChatModel, list[list[int]]]  # list of [seconds, count]
    time_window_limits: ChatModelDict[list[list[int]]] = Field(title="time_window_limits")  # list of [seconds, count]
    # available_time_range_in_day: dict[ChatModel, Optional[list[int]]]  # [start_time, end_time]
    available_time_range_in_day: ChatModelDict[Optional[list[int]]] = Field(title="available_time_range_in_day")  # [start_time, end_time]

    @staticmethod
    def default():
        return AskTimeLimits.unlimited()

    @staticmethod
    def unlimited():
        # return AskTimeLimits(
        #     time_window_limits={
        #         ChatModel.gpt_3_5: [],
        #         ChatModel.gpt_4: [],
        #     }, available_time_range_in_day={
        #         ChatModel.gpt_3_5: None,
        #         ChatModel.gpt_4: None,
        #     })
        return AskTimeLimits(
            time_window_limits=ChatModelDict(gpt_3_5=[], gpt_4=[]),
            available_time_range_in_day=ChatModelDict(gpt_3_5=None, gpt_4=None),
        )
