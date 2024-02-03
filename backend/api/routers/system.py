import random
from datetime import datetime, timedelta, timezone
import httpx
from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from sqlalchemy import select

import api.enums
import api.globals as g
from api.conf import Config, Credentials
from api.conf.config import ConfigModel
from api.conf.credentials import CredentialsModel
from api.database.sqlalchemy import get_async_session_context, get_user_db_context
from api.enums import OpenaiWebChatStatus
from api.exceptions import InvalidParamsException, OpenaiWebException
from api.models.db import User, OpenaiWebConversation
from api.models.doc import RequestLogDocument, AskLogDocument
from api.schemas import LogFilterOptions, SystemInfo, UserCreate, UserSettingSchema, OpenaiWebSourceSettingSchema, \
    OpenaiApiSourceSettingSchema, RequestLogAggregation, AskLogAggregation
from api.schemas.openai_schemas import OpenaiWebAccountsCheckResponse
from api.sources import OpenaiWebChatManager, OpenaiApiChatManager
from api.users import current_super_user, get_user_manager_context
from utils.admin import sync_conversations
from utils.logger import get_logger

logger = get_logger(__name__)
config = Config()
credentials = Credentials()

router = APIRouter()


async def count_active_users():
    async with get_async_session_context() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
    queueing_count = 0
    active_user_in_5m = 0
    active_user_in_1h = 0
    active_user_in_1d = 0
    current_time = datetime.now().astimezone(tz=timezone.utc)
    for user in users:
        if not user.last_active_time:
            continue
        if user.setting.openai_web_chat_status == OpenaiWebChatStatus.queueing:
            queueing_count += 1
        if user.is_superuser:  # 管理员不计入在线人数
            continue
        if user.last_active_time > current_time - timedelta(minutes=5):
            active_user_in_5m += 1
        if user.last_active_time > current_time - timedelta(hours=1):
            active_user_in_1h += 1
        if user.last_active_time > current_time - timedelta(days=1):
            active_user_in_1d += 1
    return active_user_in_5m, active_user_in_1h, active_user_in_1d, queueing_count, users


@cache(expire=60)
async def count_active_users_cached():
    result = await count_active_users()
    return result


@router.get("/system/info", tags=["system"], response_model=SystemInfo)
async def get_system_info(_user: User = Depends(current_super_user)):
    active_user_in_5m, active_user_in_1h, active_user_in_1d, queueing_count, users = await count_active_users()
    async with get_async_session_context() as session:
        conversations = await session.execute(select(OpenaiWebConversation))
        conversations = conversations.scalars().all()
    result = SystemInfo(
        startup_time=g.startup_time,
        total_user_count=len(users),
        total_conversation_count=len(conversations),
        valid_conversation_count=len([c for c in conversations if c.is_valid]),
    )
    return result


@router.get("/system/stats/request", tags=["system"], response_model=list[RequestLogAggregation])
@cache(expire=30)
async def get_request_statistics(
        # TODO: add filter options
        # start_query_time: Optional[datetime] = None,
        # end_query_time: Optional[datetime] = None,
        granularity: int = 1800, _user: User = Depends(current_super_user)
):
    if granularity <= 0 or granularity % 60 != 0:
        raise InvalidParamsException("Invalid granularity")

    # TODO: round float to 2 decimal places
    pipeline = [
        {
            "$project": {
                # 对齐时间到整点
                "start_time": {
                    "$toDate": {
                        "$subtract": [{"$toLong": "$time"}, {"$mod": [{"$toLong": "$time"}, granularity * 1000]}]
                    }
                },
                "route_path": "$meta.route_path",
                "method": "$meta.method",
                "user_id": 1,
                "elapsed_ms": 1
            }
        },
        {
            "$group": {
                "_id": {
                    "start_time": "$start_time",
                    "route_path": "$route_path",
                    "method": "$method"
                },
                "count": {"$sum": 1},
                "user_ids": {"$addToSet": "$user_id"},
                "avg_elapsed_ms": {"$avg": "$elapsed_ms"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    result = await RequestLogDocument.aggregate(
        pipeline
    ).to_list()

    return result


@router.get("/system/stats/ask", tags=["system"], response_model=list[AskLogAggregation])
@cache(expire=30)
async def get_ask_statistics(
        # start_query_time: Optional[datetime] = None,
        # end_query_time: Optional[datetime] = None,
        granularity: int = 1800, _user: User = Depends(current_super_user)
):
    if granularity <= 0 or granularity % 60 != 0:
        raise InvalidParamsException("Invalid granularity")

    pipeline = [
        {
            "$project": {
                # 对齐时间到整点
                "start_time": {
                    "$toDate": {
                        "$subtract": [{"$toLong": "$time"}, {"$mod": [{"$toLong": "$time"}, granularity * 1000]}]
                    }
                },
                "meta": 1,
                "user_id": 1,
                "ask_time": 1,
                "queueing_time": 1
            }
        },
        {
            "$group": {
                "_id": {
                    "start_time": "$start_time",
                    "meta": "$meta"
                },
                "count": {"$sum": 1},
                "user_ids": {"$addToSet": "$user_id"},
                "total_ask_time": {"$sum": "$ask_time"},
                "total_queueing_time": {"$sum": "$queueing_time"},
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    result = await AskLogDocument.aggregate(
        pipeline
    ).to_list()

    return result


@router.get("/system/config", tags=["system"], response_model=ConfigModel)
async def get_config(_user: User = Depends(current_super_user)):
    return config.model()


@router.put("/system/config", tags=["system"], response_model=ConfigModel)
async def update_config(config_model: ConfigModel, _user: User = Depends(current_super_user)):
    config.update(config_model)
    config.save()
    openai_web_manager = OpenaiWebChatManager()
    openai_api_manager = OpenaiApiChatManager()
    openai_web_manager.reset_session()
    openai_api_manager.reset_session()
    return config.model()


@router.get("/system/credentials", tags=["system"], response_model=CredentialsModel)
async def get_credentials(_user: User = Depends(current_super_user)):
    # TODO: 安全防范
    return credentials.model()


@router.put("/system/credentials", tags=["system"], response_model=CredentialsModel)
async def update_credentials(credentials_model: CredentialsModel, _user: User = Depends(current_super_user)):
    credentials.update(credentials_model)
    credentials.save()
    openai_web_manager = OpenaiWebChatManager()
    openai_web_manager.reset_session()
    return credentials.model()


@router.post("/system/action/sync-openai-web-conv", tags=["system"])
async def sync_openai_web_conversations(_user: User = Depends(current_super_user)):
    exception = await sync_conversations()
    if exception:
        if isinstance(exception, httpx.ConnectError):
            raise OpenaiWebException("Failed to connect to ChatGPT server. Did you set the correct chatgpt_base_url?")
        else:
            raise exception
    return None


@router.get("/system/check-openai-web-account", tags=["system"], response_model=OpenaiWebAccountsCheckResponse)
async def check_openai_web_account(_user: User = Depends(current_super_user)):
    openai_web_manager = OpenaiWebChatManager()
    response = await openai_web_manager.check_accounts()
    return response
