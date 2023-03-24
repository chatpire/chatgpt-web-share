import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select

import api.globals as g
from api.config import config
from api.database import get_async_session_context
from api.enums import ChatStatus
from api.models import User
from api.schema import ServerStatusSchema, LogFilterOptions
from api.users import current_active_user, current_super_user

router = APIRouter()

server_status_cache = None
server_status_cache_last_update_time: datetime | None = None


@router.get("/status", tags=["status"], response_model=ServerStatusSchema)
async def get_status(_user: User = Depends(current_active_user)):
    global server_status_cache
    global server_status_cache_last_update_time
    if server_status_cache is not None and server_status_cache_last_update_time is not None:
        if server_status_cache_last_update_time > datetime.utcnow() - timedelta(seconds=5):
            return server_status_cache
    async with get_async_session_context() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
    # 根据 active_time, 统计 5m/1h/1d 内的在线人数
    active_user_in_5m = 0
    active_user_in_1h = 0
    active_user_in_1d = 0
    current_time = datetime.utcnow()
    queueing_count = 0
    for user in users:
        if not user.active_time or user.is_superuser:
            continue
        if user.chat_status == ChatStatus.queueing:
            queueing_count += 1
        if user.active_time > current_time - timedelta(minutes=5):
            active_user_in_5m += 1
        if user.active_time > current_time - timedelta(hours=1):
            active_user_in_1h += 1
        if user.active_time > current_time - timedelta(days=1):
            active_user_in_1d += 1
    server_status_cache = ServerStatusSchema(
        active_user_in_5m=active_user_in_5m,
        active_user_in_1h=active_user_in_1h,
        active_user_in_1d=active_user_in_1d,
        is_chatbot_busy=g.chatgpt_manager.is_busy(),
        chatbot_waiting_count=queueing_count
    )
    server_status_cache_last_update_time = datetime.utcnow()
    return server_status_cache


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


@router.post("/logs/proxy", tags=["status"])
async def get_proxy_logs(_user: User = Depends(current_super_user), options: LogFilterOptions = LogFilterOptions()):
    lines = read_last_n_lines(
        os.path.join(config.get("log_dir", "logs"), "reverse_proxy.log"),
        options.max_lines,
        options.exclude_keywords
    )
    return lines


@router.post("/logs/server", tags=["status"])
async def get_server_logs(_user: User = Depends(current_super_user), options: LogFilterOptions = LogFilterOptions()):
    lines = read_last_n_lines(
        g.server_log_filename,
        options.max_lines,
        options.exclude_keywords
    )
    return lines
