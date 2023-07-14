from typing import Optional, Literal

from pydantic import BaseModel, validator, Field

from api.conf.base_config import BaseConfig
from api.enums import OpenaiWebChatModels, OpenaiApiChatModels
from utils.common import singleton_with_lock

_TYPE_CHECKING = False


class CommonSetting(BaseModel):
    sync_conversations_on_startup: bool = True
    sync_conversations_regularly: bool = False
    print_sql: bool = False
    create_initial_admin_user: bool = True
    initial_admin_user_username: str = 'admin'
    initial_admin_user_password: str = 'password'

    @validator("initial_admin_user_password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password too short")
        return v


class HttpSetting(BaseModel):
    host: str = '127.0.0.1'
    port: int = Field(8000, ge=1, le=65535)
    cors_allow_origins: list[str] = ['http://localhost', 'http://127.0.0.1']


class DataSetting(BaseModel):
    data_dir: str = './data'
    database_url: str = 'sqlite+aiosqlite:///data/database.db'
    mongodb_url: str = 'mongodb://cws:password@mongo:27017'  # 'mongodb://cws:password@localhost:27017'
    run_migration: bool = False

    @validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith('sqlite+aiosqlite:///'):
            raise ValueError("Only support sqlite: 'sqlite+aiosqlite:///'")
        return v


class AuthSetting(BaseModel):
    jwt_secret: str = 'MODIFY_THIS_TO_RANDOM_SECRET'
    jwt_lifetime_seconds: int = Field(86400, ge=1)
    cookie_max_age: int = Field(86400, ge=1)
    cookie_name: str = 'user_auth'
    user_secret: str = 'MODIFY_THIS_TO_RANDOM_SECRET'


class OpenaiWebChatGPTSetting(BaseModel):
    enabled: bool = True
    is_plus_account: bool = True
    chatgpt_base_url: Optional[str] = None
    proxy: Optional[str] = None
    common_timeout: int = Field(10, ge=1)  # connect, read, write
    ask_timeout: int = Field(600, ge=1)
    enabled_models: list[OpenaiWebChatModels] = ["gpt_3_5", "gpt_4", "gpt_4_browsing", "gpt_4_plugins"]
    model_code_mapping: dict[OpenaiWebChatModels, str] = {
        "gpt_3_5": "text-davinci-002-render-sha",
        "gpt_3_5_mobile": "text-davinci-002-render-sha-mobile",
        "gpt_4": "gpt-4",
        "gpt_4_mobile": "gpt-4-mobile",
        "gpt_4_browsing": "gpt-4-browsing",
        "gpt_4_plugins": "gpt-4-plugins",
    }

    @validator("chatgpt_base_url")
    def chatgpt_base_url_end_with_slash(cls, v):
        if v is not None and not v.endswith('/'):
            v += '/'
        return v


class OpenaiApiSetting(BaseModel):
    enabled: bool = True
    openai_base_url: str = 'https://api.openai.com/v1/'
    proxy: Optional[str] = None
    connect_timeout: int = Field(10, ge=1)
    read_timeout: int = Field(20, ge=1)
    enabled_models: list[OpenaiApiChatModels] = ["gpt_3_5", "gpt_4"]
    model_code_mapping: dict[OpenaiApiChatModels, str] = {
        "gpt_3_5": "gpt-3.5-turbo",
        "gpt_4": "gpt-4",
    }


class LogSetting(BaseModel):
    console_log_level: Literal['INFO', 'DEBUG', 'WARNING'] = 'INFO'


class StatsSetting(BaseModel):
    ask_stats_ttl: int = 90 * 24 * 60 * 60  # 90 days
    request_stats_ttl: int = 30 * 24 * 60 * 60  # 30 days. -1 means never expire
    request_stats_filter_keywords: list[str] = ['/status']


class ConfigModel(BaseModel):
    openai_web: OpenaiWebChatGPTSetting = OpenaiWebChatGPTSetting()
    openai_api: OpenaiApiSetting = OpenaiApiSetting()
    common: CommonSetting = CommonSetting()
    http: HttpSetting = HttpSetting()
    data: DataSetting = DataSetting()
    auth: AuthSetting = AuthSetting()
    stats: StatsSetting = StatsSetting()
    log: LogSetting = LogSetting()

    class Config:
        underscore_attrs_are_private = True


@singleton_with_lock
class Config(BaseConfig[ConfigModel]):
    if _TYPE_CHECKING:
        openai_web: OpenaiWebChatGPTSetting = OpenaiWebChatGPTSetting()
        openai_api: OpenaiApiSetting = OpenaiApiSetting()
        common: CommonSetting = CommonSetting()
        http: HttpSetting = HttpSetting()
        log: LogSetting = LogSetting()
        stats: StatsSetting = StatsSetting()
        data: DataSetting = DataSetting()
        auth: AuthSetting = AuthSetting()

    def __init__(self, load_config: bool = True):
        super().__init__(ConfigModel, "config.yaml", load_config=load_config)
