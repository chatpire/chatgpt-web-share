import contextlib
from typing import AsyncGenerator

from fastapi import Depends
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from alembic.config import Config as AlembicConfig
from alembic import command

from api.conf import Config
from api.models.db import Base, User

from utils.logger import get_logger

import json
import pydantic.json


def _custom_json_serializer(*args, **kwargs) -> str:
    """
    Encodes json in the same way that pydantic does.
    """
    return json.dumps(*args, default=pydantic.json.pydantic_encoder, **kwargs)


logger = get_logger(__name__)
config = Config()

database_url = config.data.database_url
engine = create_async_engine(database_url, echo=config.common.print_sql, json_serializer=_custom_json_serializer)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
metadata = sqlalchemy.MetaData()
alembic_cfg = AlembicConfig("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", database_url)


def run_upgrade(conn, cfg):
    cfg.attributes["connection"] = conn
    command.upgrade(cfg, "head")


def run_stamp(conn, cfg, revision):
    cfg.attributes["connection"] = conn
    command.stamp(cfg, revision)


def run_ensure_version(conn, cfg):
    cfg.attributes["connection"] = conn
    command.ensure_version(cfg)


async def create_db_and_tables():
    # 如果数据库不存在则创建数据库（数据表）；若有更新，则执行迁移
    # https://alembic.sqlalchemy.org/en/latest/autogenerate.html
    async with engine.connect() as conn:
        # 判断数据库是否存在
        def use_inspector(conn):
            inspector = sqlalchemy.inspect(conn)
            return inspector.has_table("user")

        result = await conn.run_sync(use_inspector)

        if not result:
            logger.info("database not exists, creating database...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("database created!")
            await conn.run_sync(run_stamp, alembic_cfg, "head")
            logger.info(f"stamped database to head")
            return
        else:
            await conn.run_sync(run_ensure_version, alembic_cfg)

        if config.data.run_migration:
            try:
                logger.info("try to migrate database...")
                await conn.run_sync(run_upgrade, alembic_cfg)
            except Exception as e:
                logger.warning("Database migration might fail, please check the database manually!")
                logger.warning(f"detail: {str(e)}")

        logger.info("database initialized")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


# 使得 get_async_session_context 和 get_user_db_context 可以使用async with语法

get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
