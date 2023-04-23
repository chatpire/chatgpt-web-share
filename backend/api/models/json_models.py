from typing import Optional

from pydantic import BaseModel

from api.enums import RevChatModels


class RevChatGPTAskLimits(BaseModel):
    total_count: int = -1
    per_model_count: dict[str, int] = {
        RevChatModels.default.value: 0,
        RevChatModels.gpt4.value: 0,
    }

    @staticmethod
    def unlimited():
        return RevChatGPTAskLimits(total_count=-1, per_model_count={
            RevChatModels.default.value: -1,
            RevChatModels.gpt4.value: -1,
        })


class RevChatGPTTimeLimits(BaseModel):
    time_window_limits: dict[str, list[list[int]]] = {  # list of [seconds, count]
        RevChatModels.default.value: [],
        RevChatModels.gpt4.value: [],
    }
    available_time_range_in_day: dict[str, Optional[list[int]]] = {  # [start_time, end_time]
        RevChatModels.default.value: None,
        RevChatModels.gpt4.value: None,
    }

    @staticmethod
    def unlimited():
        return RevChatGPTTimeLimits(time_window_limits={
            RevChatModels.default.value: [],
            RevChatModels.gpt4.value: [],
        }, available_time_range_in_day={
            RevChatModels.default.value: None,
            RevChatModels.gpt4.value: None,
        })
