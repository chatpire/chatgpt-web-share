from typing import Optional

from pydantic import BaseModel

from api.enums import ChatModel


class RevChatAskLimits(BaseModel):
    max_conv_count: int
    total_count: int
    per_model_count: dict[ChatModel, int]

    @staticmethod
    def default():
        return RevChatAskLimits(
            max_conv_count=1,
            total_count=0,
            per_model_count={
                ChatModel.gpt_3_5: 0,
                ChatModel.gpt_4: 0,
            })

    @staticmethod
    def unlimited():
        return RevChatAskLimits(
            max_conv_count=-1,
            total_count=-1,
            per_model_count={
                ChatModel.gpt_3_5: -1,
                ChatModel.gpt_4: -1,
            })


class RevChatTimeLimits(BaseModel):
    time_window_limits: dict[ChatModel, list[list[int]]]  # list of [seconds, count]
    available_time_range_in_day: dict[ChatModel, Optional[list[int]]]  # [start_time, end_time]

    @staticmethod
    def default():
        return RevChatTimeLimits.unlimited()

    @staticmethod
    def unlimited():
        return RevChatTimeLimits(
            time_window_limits={
                ChatModel.gpt_3_5: [],
                ChatModel.gpt_4: [],
            }, available_time_range_in_day={
                ChatModel.gpt_3_5: None,
                ChatModel.gpt_4: None,
            })
