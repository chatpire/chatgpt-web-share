import asyncio
import time
from datetime import datetime
import aiocron
from api.middlewares import AccessLoggerMiddleware, StatisticsMiddleware
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException
import api.globals as g
import os

from api.models.json_models import RevChatGPTAskLimits
from api.schema import UserCreate, UserSettingSchema
from utils.stats import dump_stats, load_stats
from utils.admin import sync_conversations, create_user
from api.enums import RevChatStatus
from api.models import User
from api.response import CustomJSONResponse, handle_exception_response
from api.database import create_db_and_tables, get_async_session_context
from api.exceptions import SelfDefinedException, UserAlreadyExists
from api.routers import users, conv, chat, system, status
from api.conf import Config
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from utils.logger import setup_logger, get_log_config, get_logger
from revChatGPT.typings import Error as revChatGPTError

config = Config().get_config()

setup_logger()

logger = get_logger(__name__)

app = FastAPI(
    default_response_class=CustomJSONResponse,
    middleware=[
        Middleware(AccessLoggerMiddleware, format='%(client_addr)s | %(request_line)s | %(status_code)s | %(M)s ms',
                   logger=get_logger("access")),
        Middleware(StatisticsMiddleware)]
)

app.include_router(users.router)
app.include_router(conv.router)
app.include_router(chat.router)
app.include_router(system.router)
app.include_router(status.router)

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


@app.exception_handler(revChatGPTError)
async def validation_exception_handler(request, exc):
    return handle_exception_response(exc)


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()
    logger.info("database initialized")
    g.startup_time = time.time()

    load_stats()

    if config.common.create_initial_admin_user:
        try:
            user = await create_user(UserCreate(
                username=config.common.initial_admin_user_username,
                nickname="admin",
                email="admin@admin.com",
                password=config.common.initial_admin_user_password,
                is_active=True,
                is_verified=True,
                is_superuser=True,
                setting=UserSettingSchema.unlimited()
            ), safe=False)
            print(user)
        except UserAlreadyExists:
            logger.info(f"admin already exists, skip creating admin user")
        except Exception as e:
            raise e

    if not config.common.sync_conversations_on_startup:
        return

    # 重置所有用户chat_status
    async with get_async_session_context() as session:
        r = await session.execute(select(User))
        results = r.scalars().all()
        for user in results:
            user.rev_chat_status = RevChatStatus.idling
            session.add(user)
        await session.commit()

    # 运行 Proxy Server
    # if config.common.run_reverse_proxy:
    #     from utils.proxy import run_reverse_proxy
    #     run_reverse_proxy()
    #     await asyncio.sleep(2)  # 等待 Proxy Server 启动

    logger.info(
        f"Using {config.chatgpt.chatgpt_base_url or 'env: ' + os.environ.get('CHATGPT_BASE_URL', '<default_bypass>')} as ChatGPT base url")

    # 获取 ChatGPT 对话，并同步数据库
    if not config.common.sync_conversations_on_startup:
        logger.info("Sync conversations on startup disabled. Jumping...")
        return  # 跳过同步对话
    else:
        await sync_conversations()

    @aiocron.crontab('*/5 * * * *', loop=asyncio.get_event_loop())
    async def cron_dump_stats():
        dump_stats(print_log=False)

    if config.common.sync_conversations_regularly:
        logger.info("Sync conversations regularly enabled, will sync conversations every 12 hours.")

        # 默认每隔 12 小时同步一次
        @aiocron.crontab('0 */12 * * *', loop=asyncio.get_event_loop())
        async def sync_conversations_regularly():
            await sync_conversations()


# 关闭时
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("On shutdown...")
    # close_reverse_proxy()
    dump_stats()


# @api.get("/routes")
# async def root():
#     url_list = [{"name": route.name, "path": route.path, "path_regex": str(route.path_regex)}
#                 for route in api.routes]
#     return PrettyJSONResponse(url_list)


if __name__ == "__main__":
    uvicorn.run(app, host=config.http.host,
                port=config.http.port,
                proxy_headers=True,
                forwarded_allow_ips='*',
                log_config=get_log_config(),
                )
