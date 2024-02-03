import uuid
from datetime import datetime
from typing import List, Optional

from fastapi_users_db_sqlalchemy import Integer
from sqlalchemy import String, Enum, Boolean, ForeignKey, func, Float
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column

from api.database.custom_types import Pydantic, UTCDateTime, GUID
from api.enums import OpenaiWebChatStatus, OpenaiWebChatModels, OpenaiApiChatModels, ChatSourceTypes
from api.models.json import UploadedFileOpenaiWebInfo, UploadedFileExtraInfo
from api.schemas import UserSettingSchema, OpenaiWebSourceSettingSchema, OpenaiApiSourceSettingSchema


# declarative base class
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="用户id")
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, comment="用户名")
    nickname: Mapped[str] = mapped_column(String(64), comment="昵称")
    email: Mapped[str]
    # openai_web_chat_status: Mapped[WebChatStatus] = mapped_column(Enum(WebChatStatus), default=WebChatStatus.idling,
    #                                                               comment="对话状态")
    last_active_time: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(timezone=True), comment="最后活跃时间")
    create_time: Mapped[datetime] = mapped_column(UTCDateTime(timezone=True),
                                                  server_default=func.now(), comment="创建时间")
    avatar: Mapped[Optional[str]] = mapped_column(comment="头像")
    valid_until: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(timezone=True), comment="用户有效期")
    remark: Mapped[Optional[str]] = mapped_column(String(256), comment="仅管理员可见的备注")
    is_superuser: Mapped[bool] = mapped_column(Boolean, comment="是否是管理员")
    is_active: Mapped[bool] = mapped_column(Boolean, comment="启用/禁用用户")
    is_verified: Mapped[bool] = mapped_column(Boolean, comment="是否已经验证")
    hashed_password: Mapped[str] = mapped_column(String(1024))

    setting: Mapped["UserSetting"] = relationship("UserSetting", back_populates="user", lazy="joined",
                                                  cascade="save-update, merge, delete, delete-orphan")
    conversations: Mapped[List["BaseConversation"]] = relationship("BaseConversation", back_populates="user")
    uploaded_files: Mapped[List["UploadedFileInfo"]] = relationship("UploadedFileInfo", back_populates="uploader",
                                                                    cascade="delete")  # TODO: 删除用户时，删除用户上传的文件


class UserSetting(Base):
    __tablename__ = "user_setting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), comment="用户id")
    user: Mapped[User] = relationship("User", back_populates="setting", lazy="joined")
    credits: Mapped[float] = mapped_column(Float, default=0, comment="积分")
    openai_web_chat_status: Mapped[OpenaiWebChatStatus] = mapped_column(Enum(OpenaiWebChatStatus),
                                                                        default=OpenaiWebChatStatus.idling,
                                                                        comment="对话状态")
    openai_web: Mapped[OpenaiWebSourceSettingSchema] = mapped_column(Pydantic(OpenaiWebSourceSettingSchema))
    openai_api: Mapped[OpenaiApiSourceSettingSchema] = mapped_column(Pydantic(OpenaiApiSourceSettingSchema))


class BaseConversation(Base):
    """
    https://docs.sqlalchemy.org/en/20/orm/inheritance.html#single-table-inheritance
    仅保留用户映射关系和基础信息，对话内容保存在mongodb中
    """

    __tablename__ = "conversation"
    __mapper_args__ = {
        "polymorphic_on": "source",
        "polymorphic_identity": "base",
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[ChatSourceTypes] = mapped_column(Enum(ChatSourceTypes), comment="对话类型")
    source_id: Mapped[Optional[str]] = mapped_column(String(256), comment="对话来源id")
    conversation_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True, unique=True, comment="uuid")
    current_model: Mapped[Optional[str]] = mapped_column(default=None, use_existing_column=True)
    title: Mapped[Optional[str]] = mapped_column(comment="对话标题")
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), comment="发起用户id")
    user: Mapped["User"] = relationship(back_populates="conversations")
    is_valid: Mapped[bool] = mapped_column(Boolean, comment="是否有效")
    create_time: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(timezone=True), comment="创建时间")
    update_time: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(timezone=True), comment="最后更新时间")


class OpenaiWebConversation(BaseConversation):
    __mapper_args__ = {
        "polymorphic_identity": "openai_web",
    }

    current_model: Mapped[Optional[Enum["OpenaiWebChatModels"]]] = mapped_column(
        Enum(OpenaiWebChatModels),
        default=None,
        use_existing_column=True)


class OpenaiApiConversation(BaseConversation):
    __mapper_args__ = {
        "polymorphic_identity": "openai_api",
    }

    current_model: Mapped[Optional[Enum["OpenaiApiChatModels"]]] = mapped_column(
        Enum(OpenaiApiChatModels),
        default=None,
        use_existing_column=True)


class UploadedFileInfo(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4, comment="uuid")
    original_filename: Mapped[str] = mapped_column(String(256), comment="原始文件名")
    size: Mapped[int] = mapped_column(Integer, comment="文件大小(bytes)")
    content_type: Mapped[Optional[str]] = mapped_column(String(256), comment="文件类型", nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(1024),
                                                        comment="文件在服务器的存储路径，相对于配置中的存储路径；为空表示未在服务器上存储，即未上传或者已清理")
    upload_time: Mapped[datetime] = mapped_column(UTCDateTime(timezone=True), default=datetime.utcnow,
                                                  comment="上传日期")
    openai_web_info: Mapped[Optional[UploadedFileOpenaiWebInfo]] = mapped_column(Pydantic(UploadedFileOpenaiWebInfo),
                                                                                 nullable=True)
    extra_info: Mapped[Optional[dict]] = mapped_column(Pydantic(UploadedFileExtraInfo), nullable=True)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("user.id"), comment="上传的用户id")
    uploader: Mapped["User"] = relationship(back_populates="uploaded_files")
