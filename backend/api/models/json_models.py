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
                RevChatModels.chatgpt_3_5: 0,
                RevChatModels.gpt_4: 0,
            })

    @staticmethod
    def unlimited():
        return RevChatAskLimits(
            max_conv_count=-1,
            total_count=-1,
            per_model_count={
                RevChatModels.chatgpt_3_5: -1,
                RevChatModels.gpt_4: -1,
            })


class RevChatTimeLimits(BaseModel):
    time_window_limits: dict[RevChatModels, list[list[int]]]  # list of [seconds, count]
    available_time_range_in_day: dict[RevChatModels, Optional[list[int]]]  # [start_time, end_time]

    @staticmethod
    def default():
        return RevChatTimeLimits(
            time_window_limits={
                RevChatModels.chatgpt_3_5: [],
                RevChatModels.gpt_4: [],
            }, available_time_range_in_day={
                RevChatModels.chatgpt_3_5: None,
                RevChatModels.gpt_4: None,
            })

    @staticmethod
    def unlimited():
        return RevChatTimeLimits(
            time_window_limits={
                RevChatModels.chatgpt_3_5.value: [],
                RevChatModels.gpt_4.value: [],
            }, available_time_range_in_day={
                RevChatModels.chatgpt_3_5.value: None,
                RevChatModels.gpt_4.value: None,
            })
