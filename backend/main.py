import asyncio
import uvicorn

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException

from os import environ

environ["CHATGPT_BASE_URL"] = environ.get("CHATGPT_BASE_URL", "https://apps.openai.com/")

import api.globals as g
from api.enums import ChatStatus
from api.models import Conversation, User
from api.response import CustomJSONResponse, PrettyJSONResponse, handle_exception_response
from api.config import config
from api.database import create_db_and_tables, get_async_session_context
from api.exceptions import SelfDefinedException
from api.routers import users, chat, status
from fastapi.middleware.cors import CORSMiddleware

from utils.create_user import create_user
import dateutil.parser
from revChatGPT.V1 import Error as ChatGPTError

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


@app.exception_handler(ChatGPTError)
async def validation_exception_handler(request, exc):
    return handle_exception_response(exc)


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

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

    # 获取 ChatGPT 对话，并同步数据库
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, g.chatgpt_manager.get_conversations)
        if result and len(result) > 0:
            print(f"获取到 {len(result)} 条对话")
            conversations_map = {conv['id']: conv for conv in result}
            async with get_async_session_context() as session:
                r = await session.execute(select(Conversation))
                results = r.scalars().all()

                for conv_db in results:
                    conv = conversations_map.get(conv_db.conversation_id, None)
                    if conv:
                        # 同步标题
                        if conv["title"] != conv_db.title:
                            conv_db.title = conv["title"]
                            print(f"对话 {conv_db.conversation_id} 标题变更：{conv_db.title}")
                            session.add(conv_db)
                        # 同步时间
                        create_time = dateutil.parser.isoparse(conv["create_time"])
                        if create_time != conv_db.create_time:
                            conv_db.create_time = create_time
                            print(f"对话 {conv_db.conversation_id} 创建时间变更：{conv_db.create_time}")
                            session.add(conv_db)
                        conversations_map.pop(conv_db.conversation_id)
                    elif not conv and conv_db.is_valid:  # 若数据库中存在，但 ChatGPT 中不存在，则将数据库中的对话标记为无效
                        conv_db.is_valid = False
                        print(f"对话 {conv_db.title}({conv_db.conversation_id}) 不存在于 ChatGPT 记录中")
                        session.add(conv_db)

                # 新增对话
                for conv in conversations_map.values():
                    new_conv = Conversation(
                        conversation_id=conv["id"],
                        title=conv["title"],
                        is_valid=True,
                        create_time=dateutil.parser.isoparse(conv["create_time"]))
                    session.add(new_conv)
                    print(f"新增对话 {conv['title']}({conv['id']})")

                await session.commit()
    except ChatGPTError as e:
        print(f"获取对话失败: {e.source} {e.code}: {e.message}")
    print("对话同步完成")


# @api.get("/routes")
# async def root():
#     url_list = [{"name": route.name, "path": route.path, "path_regex": str(route.path_regex)}
#                 for route in api.routes]
#     return PrettyJSONResponse(url_list)


if __name__ == "__main__":
    uvicorn.run(app, host=config.get("host"),
                port=config.get("port"), log_level="info")
