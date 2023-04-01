import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select

import api.globals as g
from api.config import config
from api.database import get_async_session_context
from api.enums import ChatStatus
from api.models import User, Conversation
from api.schema import ServerStatusSchema, LogFilterOptions, SystemStatistics
from api.users import current_super_user
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

check_users_cache = None
check_users_cache_last_update_time: datetime | None = None

CACHE_DURATION_SECONDS = 3


async def check_users(refresh_cache: bool = False):
    global check_users_cache
    global check_users_cache_last_update_time

    if refresh_cache:
        check_users_cache = None
        check_users_cache_last_update_time = None
    if check_users_cache is not None and check_users_cache_last_update_time is not None:
        if check_users_cache_last_update_time > datetime.utcnow() - timedelta(seconds=CACHE_DURATION_SECONDS):
            logger.debug("Using cached check_users result")
            return check_users_cache
    logger.debug("Refreshing check_users cache")
    check_users_cache_last_update_time = datetime.utcnow()
    async with get_async_session_context() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
    queueing_count = 0
    active_user_in_5m = 0
    active_user_in_1h = 0
    active_user_in_1d = 0
    current_time = datetime.utcnow()
    for user in users:
        if not user.active_time:
            continue
        if user.chat_status == ChatStatus.queueing:
            queueing_count += 1
        if user.is_superuser:  # 管理员不计入在线人数
            continue
        if user.active_time > current_time - timedelta(minutes=5):
            active_user_in_5m += 1
        if user.active_time > current_time - timedelta(hours=1):
            active_user_in_1h += 1
        if user.active_time > current_time - timedelta(days=1):
            active_user_in_1d += 1

    check_users_cache = (active_user_in_5m, active_user_in_1h, active_user_in_1d, queueing_count, users)
    return check_users_cache


@router.get("/statistics", tags=["system"], response_model=SystemStatistics)
async def get_statistics(_user: User = Depends(current_super_user)):
    active_user_in_5m, active_user_in_1h, active_user_in_1d, queueing_count, users = await check_users(
        refresh_cache=True)
    async with get_async_session_context() as session:
        conversations = await session.execute(select(Conversation))
        conversations = conversations.scalars().all()
    result = SystemStatistics(
        total_user_count=len(users),
        total_conversation_count=len(conversations),
        valid_conversation_count=len([c for c in conversations if c.is_valid]),
        server_status=ServerStatusSchema(
            active_user_in_5m=active_user_in_5m,
            active_user_in_1h=active_user_in_1h,
            active_user_in_1d=active_user_in_1d,
            is_chatbot_busy=g.chatgpt_manager.is_busy(),
            chatbot_waiting_count=queueing_count
        )
    )
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


@router.post("/logs/proxy", tags=["system"])
async def get_proxy_logs(_user: User = Depends(current_super_user), options: LogFilterOptions = LogFilterOptions()):
    lines = read_last_n_lines(
        os.path.join(config.get("log_dir", "logs"), "reverse_proxy.log"),
        options.max_lines,
        options.exclude_keywords
    )
    return lines


@router.post("/logs/server", tags=["system"])
async def get_server_logs(_user: User = Depends(current_super_user), options: LogFilterOptions = LogFilterOptions()):
    lines = read_last_n_lines(
        g.server_log_filename,
        options.max_lines,
        options.exclude_keywords
    )
    return lines
