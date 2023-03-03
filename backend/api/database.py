import contextlib
from typing import AsyncGenerator

from fastapi import Depends
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from api.config import config
from api.models import Base, User

database_url = config.get("database_url")
engine = create_async_engine(database_url, echo=config.get("print_sql", False))
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
metadata = sqlalchemy.MetaData()


async def create_db_and_tables():
    """创建数据表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


# 使得 get_async_session_context 和 get_user_db_context 可以使用async with语法

get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
