from typing import List, Optional

from fastapi_users_db_sqlalchemy import Integer, GUID, UUID_ID
from sqlalchemy import String, DateTime, Enum, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column

from api.enums import ChatStatus


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

    token_balance: Mapped[int] = mapped_column(Integer, default=0, comment="剩余token数量")
    chat_status: Mapped[ChatStatus] = mapped_column(Enum(ChatStatus), default=ChatStatus.idling, comment="对话状态")
    can_use_paid: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否可以使用paid模式")
    max_conv_count: Mapped[int] = mapped_column(Integer, default=-1, comment="最大对话数量")
    available_ask_count: Mapped[int] = mapped_column(Integer, default=-1, comment="可用的对话次数")

    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    hashed_password: Mapped[str] = mapped_column(String(1024))
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="user")


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
    use_paid: Mapped[Optional[bool]] = mapped_column(Boolean, comment="是否使用paid模型(以最后一次消息为准)")
    create_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=None, comment="创建时间")
    active_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=None, comment="最后活跃时间")
