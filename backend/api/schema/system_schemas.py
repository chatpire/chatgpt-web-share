from pydantic import BaseModel, validator

from api.conf.config_model import ChatGPTSetting, Credentials


class ServerStatusSchema(BaseModel):
    active_user_in_5m: int = None
    active_user_in_1h: int = None
    active_user_in_1d: int = None
    is_chatbot_busy: bool = None
    chatbot_waiting_count: int = None


class RequestStatistics(BaseModel):
    request_counts_interval: int
    request_counts: dict[int, list]  # {timestage: [count, [user_ids]]}
    ask_records: list  # list of (ask, time_used), timestamp.


class SystemInfo(BaseModel):
    startup_time: float
    total_user_count: int
    total_conversation_count: int
    valid_conversation_count: int


class LogFilterOptions(BaseModel):
    max_lines: int = 100
    exclude_keywords: list[str] = None

    @validator("max_lines")
    def max_lines_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("max_lines must be positive")
        return v


class ConfigRead(BaseModel):
    chatgpt: ChatGPTSetting
    credentials_exist: dict[str, bool]


class ConfigUpdate(BaseModel):
    chatgpt: ChatGPTSetting
    credentials: Credentials
