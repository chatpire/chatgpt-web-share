from pydantic import BaseModel


class RevChatGPTAskLimits(BaseModel):
    total_count: int = -1
    per_model_count: dict[str, int] = {
        "default": 0,
        "gpt4": 0,
    }


class RevChatGPTTimeLimits(BaseModel):
    time_window_limits: dict[str, list[list[int]]] = {    # list of [seconds, count]
        "default": [],
        "gpt4": [],
    }
    available_time_range_in_day: dict[str, list[int]] = {   # [start_time, end_time]
        "default": None,
        "gpt4": None,
    }
