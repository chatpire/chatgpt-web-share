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


class OpenaiChatFileUploadInfo(BaseModel):
    file_name: str
    file_size: int
    use_case: Literal['ace_upload', 'multimodal']


class OpenaiChatFileUploadUrlResponse(BaseModel):
    status: Literal["success", "error"] | str
    upload_url: Optional[str]
    file_id: Optional[str] = Field(None, description="OpenAI Web file id")
    error_code: Optional[str]
    error_message: Optional[str]


class OpenaiWebAskAttachment(BaseModel):
    name: str
    id: str
    size: int
