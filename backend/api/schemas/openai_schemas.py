from typing import Literal, Optional, Any

from pydantic import BaseModel


class OpenAIChatResponseChoice(BaseModel):
    index: Optional[int]
    message: Optional[dict[Literal["role", "content"], str]]
    delta: Optional[dict[Literal["role", "content"], str]]
    finish_reason: Optional[str]


class OpenAIChatResponseUsage(BaseModel):
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]


class OpenAIChatResponse(BaseModel):
    choices: Optional[list[OpenAIChatResponseChoice]]
    usage: Optional[OpenAIChatResponseUsage]


class OpenAIChatPluginCategory(BaseModel):
    id: Optional[str]
    title: Optional[str]


class OpenAIChatPluginManifest(BaseModel):
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


class OpenAIChatPluginUserSettings(BaseModel):
    is_authenticated: Optional[bool]
    is_installed: Optional[bool]


class OpenAIChatPlugin(BaseModel):
    id: Optional[str]
    namespace: Optional[str]
    manifest: Optional[OpenAIChatPluginManifest]
    categories: Optional[list[OpenAIChatPluginCategory]]
    domain: Optional[str]
    status: Optional[Literal['approved'] | str]
    user_settings: Optional[OpenAIChatPluginUserSettings | dict[str, Any]]  # is_authenticated, is_installed
    oauth_client_id: Optional[str]
