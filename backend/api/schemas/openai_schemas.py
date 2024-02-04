import datetime
from typing import Literal, Optional, Any

from pydantic import BaseModel, Field


class OpenaiChatResponseChoice(BaseModel):
    index: Optional[int] = None
    message: Optional[dict[Literal["role", "content"], str]] = None
    delta: Optional[dict[Literal["role", "content"], str]] = None
    finish_reason: Optional[str] = None


class OpenaiChatResponseUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class OpenaiChatResponse(BaseModel):
    choices: Optional[list[OpenaiChatResponseChoice]] = None
    usage: Optional[OpenaiChatResponseUsage] = None


class OpenaiChatPluginCategory(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None


class OpenaiChatPluginManifest(BaseModel):
    schema_version: Optional[str] = None
    name_for_model: Optional[str] = None
    name_for_human: Optional[str] = None
    description_for_model: Optional[str] = None
    description_for_human: Optional[str] = None
    api: Optional[dict[str, Any]] = None  # type openapi, url
    auth: Optional[dict[str, Any]] = None  # type none
    logo_url: Optional[str] = None
    contact_email: Optional[str] = None
    legal_info_url: Optional[str] = None


class OpenaiChatPluginUserSettings(BaseModel):
    is_authenticated: Optional[bool] = None
    is_installed: Optional[bool] = None


class OpenaiChatPlugin(BaseModel):
    id: Optional[str] = None
    namespace: Optional[str] = None
    manifest: Optional[OpenaiChatPluginManifest] = None
    categories: Optional[list[OpenaiChatPluginCategory]] = None
    domain: Optional[str] = None
    status: Optional[Literal['approved'] | str] = None
    user_settings: Optional[OpenaiChatPluginUserSettings | dict[str, Any]] = None  # is_authenticated, is_installed
    oauth_client_id: Optional[str] = None


class OpenaiChatPluginListResponse(BaseModel):
    items: list[OpenaiChatPlugin]
    count: Optional[int] = None


class OpenaiChatInterpreterInfo(BaseModel):
    kernel_started: Optional[bool] = None
    time_remaining_ms: Optional[int] = None


class OpenaiChatFileUploadUrlRequest(BaseModel):
    file_name: str
    file_size: int
    use_case: Literal['my_files', 'multimodal']


class OpenaiChatFileUploadUrlResponse(BaseModel):
    status: Literal["success", "error"] | str
    upload_url: Optional[str] = None
    file_id: Optional[str] = Field(None, description="OpenAI Web file id")
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class OpenaiWebGizmo(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    author_name: Optional[str] = None
    author: Any = None
    config: Any = None
    description: Optional[str] = None
    owner_id: Optional[str] = None
    updated_at: Optional[datetime.datetime] = None
    profile_pic_permalink: Optional[str] = None
    share_recipient: Optional[str] = None
    version: Optional[str] = None
    live_version: Optional[str] = None
    short_url: Optional[str] = None
    product_features: Any = None


class OpenaiWebCompleteRequestConversationMode(BaseModel):
    kind: Literal['primary_assistant', 'gizmo_interaction'] | str
    gizmo_id: Optional[str] = None
    gizmo: Optional[OpenaiWebGizmo] = None


class OpenaiWebCompleteRequest(BaseModel):
    action: Literal['next'] | str
    arkose_token: Optional[str] = None
    conversation_id: Optional[str] = None
    conversation_mode: Optional[OpenaiWebCompleteRequestConversationMode] = None
    force_paragen: bool = False
    force_rate_limit: bool = False
    history_and_training_disabled: bool = False
    messages: list[dict[str, Any]] | None = None
    model: str
    parent_message_id: Optional[str] = None
    plugin_ids: Optional[list[str]] = None
    suggestions: list[str] = []
    timezone_offset_min: Optional[int] = None


class OpenaiWebAccountsCheckAccountDetail(BaseModel):
    account_user_role: Literal['account-owner'] | str
    account_user_id: str
    processor: dict[str, Any]
    account_id: str
    organization_id: Optional[str] = None
    is_most_recent_expired_subscription_gratis: bool
    has_previously_paid_subscription: bool
    name: Optional[str] = None  # only for team
    profile_picture_id: Optional[str] = None
    profile_picture_url: Optional[str] = None
    structure: Literal['workspace', 'personal'] | str
    plan_type: Literal['team', 'free'] | str
    is_deactivated: bool
    promo_data: dict[str, Any]


class OpenaiWebAccountsCheckEntitlement(BaseModel):
    subscription_id: Optional[str] = None
    has_active_subscription: bool = None
    subscription_plan: Optional[Literal['chatgptteamplan', 'chatgptplusplan'] | str] = None
    expires_at: Optional[datetime.datetime] = None
    billing_period: Optional[Literal['monthly'] | str] = None


class OpenaiWebAccountsCheckAccount(BaseModel):
    account: OpenaiWebAccountsCheckAccountDetail
    features: list[str]
    entitlement: OpenaiWebAccountsCheckEntitlement
    last_active_subscription: Optional[dict[str, Any]] = None
    is_eligible_for_yearly_plus_subscription: bool


class OpenaiWebAccountsCheckResponse(BaseModel):  # accounts/check/v4-2023-04-27
    accounts: dict[str, OpenaiWebAccountsCheckAccount]
    account_ordering: list[str]
