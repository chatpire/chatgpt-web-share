import csv
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import select

import api.enums
import api.globals as g
from api.conf import Config, Credentials
from api.conf.config import ConfigModel
from api.conf.credentials import CredentialsModel
from api.database import get_async_session_context, get_user_db_context
from api.enums import OpenaiWebChatStatus
from api.exceptions import InvalidParamsException
from api.models.db import User, OpenaiWebConversation
from api.models.doc import RequestLogDocument, AskLogDocument
from api.schemas import LogFilterOptions, SystemInfo, UserCreate, UserSettingSchema, OpenaiWebSourceSettingSchema, \
    OpenaiApiSourceSettingSchema, RequestLogAggregation, AskLogAggregation
from api.users import current_super_user, get_user_manager_context
from utils.logger import get_logger

logger = get_logger(__name__)
config = Config()
credentials = Credentials()

router = APIRouter()

check_users_cache = None
check_users_cache_last_update_time: datetime | None = None

CACHE_DURATION_SECONDS = 0  # currently do not cache, for there seems no significant performance improvement


async def check_users(refresh_cache: bool = False):
    global check_users_cache
    global check_users_cache_last_update_time

    if refresh_cache:
        check_users_cache = None
        check_users_cache_last_update_time = None
    if check_users_cache is not None and check_users_cache_last_update_time is not None:
        if check_users_cache_last_update_time > datetime.utcnow() - timedelta(seconds=CACHE_DURATION_SECONDS):
            # logger.debug("Using cached check_users result")
            return check_users_cache
    # logger.debug("Refreshing check_users cache")
    check_users_cache_last_update_time = datetime.utcnow()
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

    check_users_cache = (active_user_in_5m, active_user_in_1h, active_user_in_1d, queueing_count, users)
    return check_users_cache


@router.get("/system/info", tags=["system"], response_model=SystemInfo)
async def get_system_info(_user: User = Depends(current_super_user)):
    active_user_in_5m, active_user_in_1h, active_user_in_1d, queueing_count, users = await check_users(
        refresh_cache=True)
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


FAKE_REQ_START_TIMESTAMP = 1672502400  # 2023-01-01 00:00:00


def make_fake_requests_count(total=100, max=500):
    result = {}
    start_stage = FAKE_REQ_START_TIMESTAMP // config.stats.request_counts_interval
    for i in range(total):
        result[start_stage + i] = [random.randint(0, max), [1]]
    return result


def make_fake_ask_records(total=100, days=2):
    result = []
    model_names = list(api.enums.models.OpenaiWebChatModels)
    for i in range(total):
        ask_time = random.random() * 60 + 1
        total_time = ask_time + random.random() * 30
        result.append([
            [
                # random.randint(1, 10),  # user_id
                1,
                model_names[random.randint(0, len(model_names) - 1)],  # model_name
                ask_time,
                total_time
            ],
            FAKE_REQ_START_TIMESTAMP + random.random() * 60 * 60 * 24 * days,  # ask_time
        ])
    return result


@router.get("/system/stats/request", tags=["system"], response_model=list[RequestLogAggregation])
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


def read_last_n_lines(file_path, n, exclude_key_words=None):
    if exclude_key_words is None:
        exclude_key_words = []
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()[::-1]
    except FileNotFoundError:
        return [f"File not found: {file_path}"]
    last_n_lines = []
    for line in lines:
        if len(last_n_lines) >= n:
            break
        if any([line.find(key_word) != -1 for key_word in exclude_key_words]):
            continue
        last_n_lines.append(line)
    return last_n_lines[::-1]


@router.post("/system/logs/server", tags=["system"])
async def get_server_logs(_user: User = Depends(current_super_user), options: LogFilterOptions = LogFilterOptions()):
    lines = read_last_n_lines(
        g.server_log_filename,
        options.max_lines,
        options.exclude_keywords
    )
    return lines


@router.get("/system/config", tags=["system"], response_model=ConfigModel)
async def get_config(_user: User = Depends(current_super_user)):
    return config.model()


@router.put("/system/config", tags=["system"], response_model=ConfigModel)
async def update_config(config_model: ConfigModel, _user: User = Depends(current_super_user)):
    config.update(config_model)
    config.save()
    return config.model()


@router.get("/system/credentials", tags=["system"], response_model=CredentialsModel)
async def get_credentials(_user: User = Depends(current_super_user)):
    # TODO: 安全防范
    return credentials.model()


@router.put("/system/credentials", tags=["system"], response_model=CredentialsModel)
async def update_credentials(credentials_model: CredentialsModel, _user: User = Depends(current_super_user)):
    credentials.update(credentials_model)
    credentials.save()
    return credentials.model()


@router.post("/system/import-users", tags=["system"])
async def import_users(file: UploadFile = File(...), _user: User = Depends(current_super_user)):
    """
    解析csv文件，导入用户
    csv字段：
    """
    headers = ["id", "username", "nickname", "email", "active_time", "chat_status", "can_use_paid", "max_conv_count",
               "available_ask_count", "is_superuser", "is_active", "is_verified", "hashed_password", "can_use_gpt4",
               "available_gpt4_ask_count"]
    content = await file.read()
    content = content.decode("utf-8")
    reader = csv.DictReader(content.splitlines())
    # check headers
    for field in headers:
        if field not in reader.fieldnames:
            raise InvalidParamsException(f"Invalid csv file, missing field: {field}")
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                for row in reader:
                    user_create = UserCreate(
                        username=row["username"],
                        nickname=row["nickname"],
                        email=f"{row['username']}@example.com",
                        password="12345678",
                        remark=row["email"]
                    )
                    await user_manager._check_username_unique(user_create.username)
                    user_dict = user_create.dict()

                    del user_dict["password"]
                    user_dict["hashed_password"] = row["hashed_password"]

                    user_setting = UserSettingSchema(
                        credits=0,
                        openai_web=OpenaiWebSourceSettingSchema.default(),
                        openai_api=OpenaiApiSourceSettingSchema.default(),
                    )
                    user_setting.openai_web.available_models = ["gpt_3_5", "gpt_4"]
                    if not row["can_use_gpt4"]:
                        user_setting.openai_web.available_models = ["gpt_3_5"]
                    user_setting.openai_web.per_model_ask_count.gpt_3_5 = max(
                        int(row["available_ask_count"]) - int(row["available_gpt4_ask_count"]), 0)
                    user_setting.openai_web.per_model_ask_count.gpt_4 = int(row["available_gpt4_ask_count"])
                    user_setting.openai_web.max_conv_count = int(row["max_conv_count"])

                    await user_manager.create_with_user_dict(user_dict, user_setting)
