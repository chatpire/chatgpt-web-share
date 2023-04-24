from typing import Optional

from pydantic import BaseModel

from api.enums import RevChatModels


class RevChatAskLimits(BaseModel):
    max_conv_count: int
    total_count: int
    per_model_count: dict[RevChatModels, int]

    @staticmethod
    def default():
        return RevChatAskLimits(
            max_conv_count=1,
            total_count=0,
            per_model_count={
                RevChatModels.default: 0,
                RevChatModels.gpt4: 0,
            })

    @staticmethod
    def unlimited():
        return RevChatAskLimits(
            max_conv_count=-1,
            total_count=-1,
            per_model_count={
                RevChatModels.default: -1,
                RevChatModels.gpt4: -1,
            })


class RevChatTimeLimits(BaseModel):
    time_window_limits: dict[RevChatModels, list[list[int]]]  # list of [seconds, count]
    available_time_range_in_day: dict[RevChatModels, Optional[list[int]]]  # [start_time, end_time]

    @staticmethod
    def default():
        return RevChatTimeLimits(
            time_window_limits={
                RevChatModels.default: [],
                RevChatModels.gpt4: [],
            }, available_time_range_in_day={
                RevChatModels.default: None,
                RevChatModels.gpt4: None,
            })

    @staticmethod
    def unlimited():
        return RevChatTimeLimits(
            time_window_limits={
                RevChatModels.default.value: [],
                RevChatModels.gpt4.value: [],
            }, available_time_range_in_day={
                RevChatModels.default.value: None,
                RevChatModels.gpt4.value: None,
            })
