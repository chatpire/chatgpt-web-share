import uuid
import datetime
from typing import List
from fastapi_users import schemas
from pydantic import Field, BaseModel

from api.enums import ChatStatus


class UserRead(schemas.BaseUser[int]):
    id: int
    username: str
    nickname: str
    email: str
    active_time: datetime.datetime | None

    chat_status: ChatStatus

    can_use_paid: bool
    max_conv_count: int | None
    available_ask_count: int | None

    is_superuser: bool
    is_active: bool
    is_verified: bool


class LimitSchema(BaseModel):
    can_use_paid: bool | None = None
    max_conv_count: int | None = None
    available_ask_count: int | None = None


class UserUpdate(schemas.BaseUser[int]):
    nickname: str
    email: str = None


class UserCreate(schemas.BaseUserCreate):
    username: str
    nickname: str
    email: str
    can_use_paid: bool = False
    max_conv_count: int = -1
    available_ask_count: int = -1

    class Config:
        orm_mode = True


class ConversationSchema(BaseModel):
    id: int = -1
    conversation_id: uuid.UUID = None
    title: str = None
    user_id: int = None
    is_valid: bool = None
    is_public: bool = None
    use_paid: bool = None
    create_time: datetime.datetime = None
    active_time: datetime.datetime = None


class ServerStatusSchema(BaseModel):
    active_user_in_5m: int = None
    active_user_in_1h: int = None
    active_user_in_1d: int = None
    is_chatbot_busy: bool = None
    chatbot_waiting_count: int = None
