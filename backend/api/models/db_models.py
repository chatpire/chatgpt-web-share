from typing import List, Optional

from fastapi_users_db_sqlalchemy import Integer, GUID, UUID_ID
from sqlalchemy import String, DateTime, Enum, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column

from api.enums import RevChatStatus, ChatModels
from api.models.json_models import RevChatGPTAskLimits, RevChatGPTTimeLimits


# declarative base class
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="用户id")
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, comment="用户名")
    nickname: Mapped[str] = mapped_column(String(64), comment="昵称")
    email: Mapped[str]
    chat_status: Mapped[RevChatStatus] = mapped_column(Enum(RevChatStatus), default=RevChatStatus.idling, comment="对话状态")
    active_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=None, comment="最后活跃时间")
    created_time: Mapped[DateTime] = mapped_column(DateTime, comment="创建时间")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否是管理员")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="启用/禁用用户")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已经验证")

    avatar: Mapped[Optional[str]] = mapped_column(String(256), default=None, comment="头像")
    hashed_password: Mapped[str] = mapped_column(String(1024))

    setting: Mapped["UserSetting"] = relationship("UserSetting", back_populates="user")
    rev_conversations: Mapped[List["RevConversation"]] = relationship("RevConversation", back_populates="user")


class UserSetting(Base):
    __tablename__ = "user_setting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), comment="用户id")
    user: Mapped["User"] = relationship(back_populates="setting")

    # ChatGPT 账号相关
    can_use_revchatgpt: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否可以使用chatgpt账号对话")
    revchatgpt_available_models: Mapped[List[str]] = mapped_column(
        JSON, default=[ChatModels.default.value, ChatModels.gpt4.value], comment="chatgpt账号可用的模型")
    revchatgpt_ask_limits: Mapped[RevChatGPTAskLimits] = mapped_column(
        JSON, default=RevChatGPTAskLimits().dict(), comment="chatgpt账号对话限制")
    revchatgpt_time_limits: Mapped[RevChatGPTTimeLimits] = mapped_column(
        JSON, default=RevChatGPTTimeLimits().dict(), comment="chatgpt账号时间频率限制")

    # OpenAI API 相关
    can_use_openai_api: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否可以使用服务端OpenAI API")
    openai_api_credits: Mapped[float] = mapped_column(Float, default=0, comment="可用的OpenAI API积分")
    openai_api_available_models: Mapped[List[str]] = mapped_column(
        JSON, default=[ChatModels.default.value], comment="OpenAI API可用的模型")
    can_use_custom_openai_api: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否可以使用自定义API")
    custom_openai_api_key: Mapped[str] = mapped_column(String, default=None, comment="自定义OpenAI API key")


class RevConversation(Base):
    """
    ChatGPT 非官方 API 所使用的对话，使用 revChatGPT
    只记录对话和用户之间的对应关系，不存储内容
    """

    __tablename__ = "account_conversation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True, unique=True, comment="uuid")
    title: Mapped[Optional[str]] = mapped_column(comment="对话标题")
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), comment="发起用户id")
    user: Mapped["User"] = relationship(back_populates="rev_conversations")
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否有效")
    model_name: Mapped[Optional[Enum["ChatModels"]]] = mapped_column(
        Enum(ChatModels, values_callable=lambda obj: [e.value for e in obj] if obj else None), default=None,
        comment="使用的模型")
    created_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=None, comment="创建时间")
    active_time: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=None, comment="最后活跃时间")
