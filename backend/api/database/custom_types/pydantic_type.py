import json
from typing import Type, Any, Optional

import sqlalchemy
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import Dialect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.type_api import _T


class Pydantic(sqlalchemy.types.TypeDecorator):
    """Pydantic type.
    SAVING:
    - Uses SQLAlchemy JSON type under the hood.
    - Acceps the pydantic model and converts it to a dict on save.
    - SQLAlchemy engine JSON-encodes the dict to a string.
    RETRIEVING:
    - Pulls the string from the database.
    - SQLAlchemy engine JSON-decodes the string to a dict.
    - Uses the dict to create a pydantic model.

    https://roman.pt/posts/pydantic-in-sqlalchemy-fields/
    """

    @property
    def python_type(self) -> Type[Any]:
        return BaseModel

    def process_literal_param(self, value: Optional[_T], dialect: Dialect) -> str:
        if value is None:
            return "NULL"
        else:
            # 将 Pydantic 对象转换为 JSON 字符串
            json_str = json.dumps(jsonable_encoder(value))
            if dialect.name == "postgresql":
                # 对于 PostgreSQL，需要用 E'' 引用 JSON 字符串（未测试）
                return f"E'{json_str}'"
            else:
                # 对于其他数据库，使用单引号引用 JSON 字符串
                return f"'{json_str}'"

    impl = sqlalchemy.types.JSON

    def __init__(self, pydantic_type):
        super().__init__()
        self.pydantic_type = pydantic_type

    def load_dialect_impl(self, dialect):
        # Use JSONB for PostgreSQL and JSON for other databases.
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(sqlalchemy.JSON())

    def process_bind_param(self, value, dialect):
        # return value.dict() if value else None
        return jsonable_encoder(value) if value else None

    def process_result_value(self, value, dialect):
        return self.pydantic_type.model_validate(value) if value else None
