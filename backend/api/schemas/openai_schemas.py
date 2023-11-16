import datetime
from typing import Literal, Optional, Any

from pydantic import BaseModel, Field


class OpenaiChatResponseChoice(BaseModel):
    index: Optional[int]
    message: Optional[dict[Literal["role", "content"], str]]
    delta: Optional[dict[Literal["role", "content"], str]]
    finish_reason: Optional[str]


class OpenaiChatResponseUsage(BaseModel):
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]


class OpenaiChatResponse(BaseModel):
    choices: Optional[list[OpenaiChatResponseChoice]]
    usage: Optional[OpenaiChatResponseUsage]


class OpenaiChatPluginCategory(BaseModel):
    id: Optional[str]
    title: Optional[str]


class OpenaiChatPluginManifest(BaseModel):
    api: Optional[dict[str, Any]]  # type openapi, url
    auth: Optional[dict[str, Any]]  # type none
    logo_url: Optional[str]
    contact_email: Optional[str]
    schema_version: Optional[str]
    name_for_model: Optional[str]
    name_for_human: Optional[str]
    description_for_model: Optional[str]
    description_for_human: Optional[str]
    legal_info_url: Optional[str]


class OpenaiChatPluginUserSettings(BaseModel):
    is_authenticated: Optional[bool]
    is_installed: Optional[bool]


class OpenaiChatPlugin(BaseModel):
    id: Optional[str]
    namespace: Optional[str]
    manifest: Optional[OpenaiChatPluginManifest]
    categories: Optional[list[OpenaiChatPluginCategory]]
    domain: Optional[str]
    status: Optional[Literal['approved'] | str]
    user_settings: Optional[OpenaiChatPluginUserSettings | dict[str, Any]]  # is_authenticated, is_installed
    oauth_client_id: Optional[str]


class OpenaiChatInterpreterInfo(BaseModel):
    kernel_started: Optional[bool]
    time_remaining_ms: Optional[int]


class OpenaiChatFileUploadUrlRequest(BaseModel):
    file_name: str
    file_size: int
    use_case: Literal['my_files', 'multimodal']


class OpenaiChatFileUploadUrlResponse(BaseModel):
    status: Literal["success", "error"] | str
    upload_url: Optional[str]
    file_id: Optional[str] = Field(None, description="OpenAI Web file id")
    error_code: Optional[str]
    error_message: Optional[str]


class OpenaiWebGizmo(BaseModel):
    id: Optional[str]
    name: Optional[str]
    author_name: Optional[str]
    author: Any
    config: Any
    description: Optional[str]
    owner_id: Optional[str]
    updated_at: Optional[datetime.datetime]
    profile_pic_permalink: Optional[str]
    share_recipient: Optional[str]
    version: Optional[str]
    live_version: Optional[str]
    short_url: Optional[str]
    product_features: Any


class OpenaiWebCompleteRequestConversationMode(BaseModel):
    kind: Literal['primary_assistant', 'gizmo_interaction'] | str
    gizmo_id: Optional[str]
    gizmo: Optional[OpenaiWebGizmo]


class OpenaiWebCompleteRequest(BaseModel):
    action: Literal['next'] | str
    arkose_token: Optional[str] = None
    conversation_id: Optional[str]
    conversation_mode: Optional[OpenaiWebCompleteRequestConversationMode]
    force_paragen: bool = False
    force_rate_limit: bool = False
    history_and_training_disabled: bool = False
    messages: list[dict[str, Any]]
    model: str
    parent_message_id: Optional[str]
    plugin_ids: Optional[list[str]]
    suggestions: list[str] = []
    timezone_offset_min: Optional[int]
