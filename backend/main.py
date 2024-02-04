import asyncio
import os
import time
from contextlib import asynccontextmanager

import aiocron
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from pydantic import EmailStr
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException

import api.globals as g
from api.database.sqlalchemy import initialize_db, get_async_session_context, get_user_db_context
from api.database.mongodb import init_mongodb
from api.enums import OpenaiWebChatStatus
from api.exceptions import SelfDefinedException, UserAlreadyExists
from api.middlewares import AccessLoggerMiddleware, StatisticsMiddleware
from api.models.db import User
from api.response import CustomJSONResponse, handle_exception_response
from api.routers import users, conv, chat, system, status, files, logs
from api.schemas import UserCreate, UserSettingSchema
from api.sources import OpenaiWebChatManager
from api.users import get_user_manager_context
from utils.admin import sync_conversations
from utils.logger import setup_logger, get_log_config, get_logger
from api.conf import Config

config = Config()

setup_logger()

logger = get_logger(__name__)

if config.log.console_log_level != "DEBUG":
    import warnings

    warnings.filterwarnings("ignore")


async def startup():
    await initialize_db()
    await init_mongodb()

    FastAPICache.init(InMemoryBackend())

    g.startup_time = time.time()

    # 初始化 chatgpt_manager
    g.chatgpt_manager = OpenaiWebChatManager()

    if config.common.create_initial_admin_user:
        try:
            async with get_async_session_context() as session:
                async with get_user_db_context(session) as user_db:
                    async with get_user_manager_context(user_db) as user_manager:
                        user = await user_manager.create(UserCreate(
                            username=config.common.initial_admin_user_username,
                            nickname="admin",
                            email="admin@admin.com",
                            password=config.common.initial_admin_user_password,
                            is_active=True,
                            is_verified=True,
                            is_superuser=True,
                        ), user_setting=UserSettingSchema.unlimited(), safe=False)
            print(user)
        except UserAlreadyExists:
            logger.debug(f"admin already exists, skip creating admin user")
        except Exception as e:
            raise e

    # 重置所有用户 chat_status
    async with get_async_session_context() as session:
        r = await session.execute(select(User))
        results = r.scalars().all()
        for user in results:
            user.setting.openai_web_chat_status = OpenaiWebChatStatus.idling
            session.add(user.setting)
        await session.commit()

    if config.openai_web.chatgpt_base_url is None:
        logger.error("chatgpt_base_url is not set in config!")
        exit(1)
    else:
        logger.info(
            f"Using {config.openai_web.chatgpt_base_url} as ChatGPT base url")

    # 获取 ChatGPT 对话，并同步数据库
    if not config.openai_web.sync_conversations_on_startup:
        logger.info("Sync conversations on startup disabled.")
        return
    else:
        await sync_conversations()

    if config.openai_web.sync_conversations_schedule:
        logger.info("Sync conversations regularly enabled, will sync conversations every 12 hours.")

        interval = config.openai_web.sync_conversations_schedule_interval_hours

        @aiocron.crontab(f'0 */{interval} * * *', loop=asyncio.get_event_loop())
        async def sync_conversations_regularly():
            await sync_conversations()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield


app = FastAPI(
    lifespan=lifespan,
    default_response_class=CustomJSONResponse,
    middleware=[
        Middleware(AccessLoggerMiddleware, format='%(client_addr)s | %(request_line)s | %(status_code)s | %(M)s ms',
                   logger=get_logger("access")),
        Middleware(StatisticsMiddleware, filter_keywords=config.stats.request_stats_filter_keywords)]
)

app.include_router(users.router)
app.include_router(conv.router)
app.include_router(chat.router)
app.include_router(system.router)
app.include_router(logs.router)
app.include_router(status.router)
app.include_router(files.router)

# 解决跨站问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.http.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return handle_exception_response(exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return handle_exception_response(exc)


@app.exception_handler(SelfDefinedException)
async def validation_exception_handler(request, exc):
    return handle_exception_response(exc)


if __name__ == "__main__":
    uvicorn.run(app, host=config.http.host,
                port=config.http.port,
                proxy_headers=True,
                forwarded_allow_ips='*',
                log_config=get_log_config(),
                )
