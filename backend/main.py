import asyncio

from httpx import HTTPError
import uvicorn

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.config import config
import os

if config.get("chatgpt_base_url"):
    os.environ["CHATGPT_BASE_URL"] = config.get("chatgpt_base_url")

import api.globals as g
from api.enums import ChatStatus
from api.models import Conversation, User
from api.response import CustomJSONResponse, PrettyJSONResponse, handle_exception_response
from api.database import create_db_and_tables, get_async_session_context
from api.exceptions import SelfDefinedException
from api.routers import users, chat, status
from fastapi.middleware.cors import CORSMiddleware

from utils.logger import setup_logger, get_log_config, get_logger
from utils.proxy import close_reverse_proxy
from utils.create_user import create_user

import dateutil.parser
from revChatGPT.typing import Error as revChatGPTError

setup_logger()

logger = get_logger(__name__)

app = FastAPI(default_response_class=CustomJSONResponse)

app.include_router(users.router)
app.include_router(chat.router)
app.include_router(status.router)

origins = [
    "http://localhost",
    "http://localhost:4000",
]

# 解决跨站问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 定义若干异常处理器


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

    if config.get("create_initial_admin_user", False):
        await create_user(config.get("initial_admin_username"),
                          "admin",
                          "admin@admin.com",
                          config.get("initial_admin_password"),
                          is_superuser=True)

    if config.get("create_initial_user", False):
        await create_user(config.get("initial_user_username"),
                          "user",
                          "user@user.com",
                          config.get("initial_user_password"),
                          is_superuser=False)

    if not config.get("sync_conversations_on_startup", True):
        return

    # 重置所有用户chat_status
    async with get_async_session_context() as session:
        r = await session.execute(select(User))
        results = r.scalars().all()
        for user in results:
            user.chat_status = ChatStatus.idling
            session.add(user)
        await session.commit()

    # 运行 Proxy Server
    if config.get("run_reverse_proxy", False):
        from utils.proxy import run_reverse_proxy
        run_reverse_proxy()
        await asyncio.sleep(2)  # 等待 Proxy Server 启动

    # 获取 ChatGPT 对话，并同步数据库
    if not config.get("sync_conversations_on_startup", True):
        logger.info("Sync conversations on startup disabled. Jumping...")
        return # 跳过同步对话
    try:
        logger.debug(f"Using {os.environ.get('CHATGPT_BASE_URL', '<default_bypass>')} as ChatGPT base url")
        result = await g.chatgpt_manager.get_conversations()
        logger.info(f"Fetched {len(result)} conversations")
        openai_conversations_map = {conv['id']: conv for conv in result}
        async with get_async_session_context() as session:
            r = await session.execute(select(Conversation))
            results = r.scalars().all()

            for conv_db in results:
                openai_conv = openai_conversations_map.get(conv_db.conversation_id, None)
                if openai_conv:
                    # 同步标题
                    if openai_conv["title"] != conv_db.title:
                        conv_db.title = openai_conv["title"]
                        logger.info(f"Conversation {conv_db.conversation_id} title changed: {conv_db.title}")
                        session.add(conv_db)
                    # 同步时间
                    create_time = dateutil.parser.isoparse(openai_conv["create_time"])
                    if create_time != conv_db.create_time:
                        conv_db.create_time = create_time
                        logger.info(f"Conversation {conv_db.conversation_id} created time changed：{conv_db.create_time}")
                        session.add(conv_db)
                    openai_conversations_map.pop(conv_db.conversation_id)
                else:
                    if conv_db.is_valid:  # 若数据库中存在，但 ChatGPT 中不存在，则将数据库中的对话标记为无效
                        conv_db.is_valid = False
                        logger.info(
                            f"Conversation {conv_db.title}({conv_db.conversation_id}) is not valid, marked as invalid")
                        session.add(conv_db)

            # 新增对话
            for openai_conv in openai_conversations_map.values():
                new_conv = Conversation(
                    conversation_id=openai_conv["id"],
                    title=openai_conv["title"],
                    is_valid=True,
                    create_time=dateutil.parser.isoparse(openai_conv["create_time"])
                )
                session.add(new_conv)
                logger.info(
                    f"Conversation {conv_db.title}({conv_db.conversation_id}) not recorded, added to database")

            await session.commit()
    except revChatGPTError as e:
        logger.error(f"Fetch conversation error (ChatGPTError): {e.source} {e.code}: {e.message}")
        logger.warning("Sync conversations on startup failed!")
    except HTTPError as e:
        logger.error(f"Fetch conversation error (httpx.HTTPError): {str(e)}")
        logger.warning("Sync conversations on startup failed!")
    except Exception as e:
        logger.error(f"Fetch conversation error (unknown): {str(e)}")
        logger.warning("Sync conversations on startup failed!")


# 关闭时
@app.on_event("shutdown")
async def on_shutdown():
    close_reverse_proxy()

# @api.get("/routes")
# async def root():
#     url_list = [{"name": route.name, "path": route.path, "path_regex": str(route.path_regex)}
#                 for route in api.routes]
#     return PrettyJSONResponse(url_list)


if __name__ == "__main__":
    uvicorn.run(app, host=config.get("host"),
                port=config.get("port"),
                proxy_headers=True,
                forwarded_allow_ips='*',
                log_config=get_log_config())
