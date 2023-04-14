from typing import List, Optional

from fastapi_users_db_sqlalchemy import Integer, GUID, UUID_ID
from sqlalchemy import String, DateTime, Enum, Boolean, Float, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column

from api.enums import ChatStatus, ChatModels

import json

# declarative base class
class Base(DeclarativeBase):
    pass


class User(Base):
    """
    用户表
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="用户id")
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, comment="用户名")
    nickname: Mapped[str] = mapped_column(String(64), comment="昵称")
    email: Mapped[str]
    active_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=None, comment="最后活跃时间")

    chat_status: Mapped[ChatStatus] = mapped_column(Enum(ChatStatus), default=ChatStatus.idling, comment="对话状态")
    can_use_paid: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否可以使用paid模型")
    can_use_gpt4: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否可以使用gpt4模型")
    max_conv_count: Mapped[int] = mapped_column(Integer, default=-1, comment="最大对话数量")
    available_ask_count: Mapped[int] = mapped_column(Integer, default=-1, comment="可用的对话次数")
    available_gpt4_ask_count: Mapped[int] = mapped_column(Integer, default=-1, comment="可用的gpt4对话次数")

    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    hashed_password: Mapped[str] = mapped_column(String(1024))
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="user")
    user_apis: Mapped[List["UserApi"]] = relationship("UserApi", back_populates="user")

class Conversation(Base):
    """
    ChatGPT 非官方 API 所使用的对话
    只记录对话和用户之间的对应关系，不存储内容
    """

    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)
    title: Mapped[Optional[str]] = mapped_column(comment="对话标题")
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), comment="发起用户id")
    user: Mapped["User"] = relationship(back_populates="conversations")
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否有效")
    model_name: Mapped[Optional[Enum["ChatModels"]]] = mapped_column(
        Enum(ChatModels, values_callable=lambda obj: [e.value for e in obj] if obj else None), default=None, comment="使用的模型")
    create_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=None, comment="创建时间")
    active_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=None, comment="最后活跃时间")
    state: Mapped[Optional[list]] = mapped_column(JSON, comment="完整对话dict")


class Api(Base):
    __tablename__ = "api"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(comment="api类型")
    key: Mapped[str] = mapped_column(comment="api key")
    endpoint: Mapped[Optional[str]] = mapped_column(comment="api key")
    models: Mapped[Optional[dict]] = mapped_column(JSON, comment="支持的models")
    users = relationship("UserApi", back_populates="api")
    

class UserApi(Base):
    __tablename__ = "user_api"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), comment="发起用户id")
    user: Mapped["User"] = relationship(back_populates="user_apis")
    api_id: Mapped[Optional[int]] = mapped_column(ForeignKey("api.id"), comment="api id")
    api: Mapped["Api"] = relationship(back_populates="users")
    models: Mapped[Optional[dict]] = mapped_column(JSON, comment="支持的models")

