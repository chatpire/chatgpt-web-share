from typing import Optional, Literal

from pydantic import BaseModel, validator, Field

from api.conf.base_config import BaseConfig
from utils.common import singleton_with_lock

_TYPE_CHECKING = False


class CommonSetting(BaseModel):
    print_sql: bool = False
    create_initial_admin_user: bool = True
    initial_admin_user_username: str = 'admin'
    initial_admin_user_password: str = 'password'
    sync_conversations_on_startup: bool = True
    sync_conversations_regularly: bool = True

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
    is_plus_account: bool = False
    chatgpt_base_url: Optional[str] = None
    common_timeout: int = Field(10, ge=1)   # connect, read, write
    ask_timeout: int = Field(600, ge=1)

    @validator("chatgpt_base_url")
    def chatgpt_base_url_end_with_slash(cls, v):
        if v is not None and not v.endswith('/'):
            v += '/'
        return v


class OpenaiAPISetting(BaseModel):
    openai_base_url: str = 'https://api.openai.com/v1/'
    connect_timeout: int = Field(10, ge=1)
    read_timeout: int = Field(20, ge=1)


class LogSetting(BaseModel):
    console_log_level: Literal['INFO', 'DEBUG', 'WARNING'] = 'INFO'


class StatsSetting(BaseModel):
    ask_stats_ttl: int = 90 * 24 * 60 * 60  # 90 days
    request_stats_ttl: int = 30 * 24 * 60 * 60  # 30 days. -1 means never expire
    request_stats_filter_keywords: list[str] = ['/status']


class ConfigModel(BaseModel):
    openai_web: OpenaiWebChatGPTSetting = OpenaiWebChatGPTSetting()
    openai_api: OpenaiAPISetting = OpenaiAPISetting()
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
        openai_api: OpenaiAPISetting = OpenaiAPISetting()
        common: CommonSetting = CommonSetting()
        http: HttpSetting = HttpSetting()
        openai_web: OpenaiWebChatGPTSetting = OpenaiWebChatGPTSetting()
        log: LogSetting = LogSetting()
        stats: StatsSetting = StatsSetting()
        data: DataSetting = DataSetting()
        auth: AuthSetting = AuthSetting()

    def __init__(self):
        super().__init__(ConfigModel, "config.yaml")
