import json
import typing
from typing import Optional, Any, Generic, TypeVar, Dict

import httpx
from fastapi import Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi_users.router import ErrorCode
from pydantic import BaseModel, ValidationError
from starlette.background import BackgroundTask
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.exceptions import SelfDefinedException
from utils.common import desensitize

T = TypeVar('T')


class ResponseWrapper(BaseModel, Generic[T]):
    """
    使用自定义的返回格式：
    - 统一状态码为 200
    - 统一返回格式为 {"code", "message", "result"}
    - code 为 200 表示成功，其余表示失败。
        -1 表示一般失败
        401 表示登陆超时，需要重新登陆
        对于有状态码的错误，使用该状态码
    """

    code: int = 0
    message: str = ""
    result: Optional[T | Any] = None


class CustomJSONResponse(Response):
    media_type = "application/json"

    def __init__(
            self,
            content: Any,
            status_code: int = 200,
            headers: Optional[Dict[str, str]] = None,
            media_type: Optional[str] = None,
            background: Optional[BackgroundTask] = None,
    ) -> None:
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: typing.Any) -> bytes:
        if not isinstance(content, ResponseWrapper):
            content = ResponseWrapper(code=self.status_code, message=get_http_message(self.status_code), result=content)
        result = json.dumps(jsonable_encoder(content), ensure_ascii=False)
        return result.encode("utf-8")


class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            jsonable_encoder(content),
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")


def response(code: int = 200, message: str = "", result: Optional[Any] = None,
             headers: Optional[Dict[str, str]] = None) -> CustomJSONResponse:
    return CustomJSONResponse(
        content=ResponseWrapper(code=code, message=message, result=result),
        status_code=200,
        headers=headers
    )


def get_http_message(status_code: int) -> str:
    return {
        200: "tips.requestSuccess",
        201: "tips.requestSuccess",
        204: "tips.requestSuccess",
        400: "errors.badCredentials",
        401: "errors.userNotLogin",
        # 404: "资源不存在",
        # 502: "上游请求失败",
        -1: "失败",
    }.get(status_code, "")


def handle_exception_response(e: Exception) -> CustomJSONResponse:
    if isinstance(e, ValidationError):
        return response(-1, f"errors.validationError", e.errors())
    elif isinstance(e, SelfDefinedException):
        return response(e.code, e.reason, desensitize(e.message))
    elif isinstance(e, StarletteHTTPException):
        if e.detail == ErrorCode.REGISTER_USER_ALREADY_EXISTS:
            tip = "errors.userAlreadyExists"
        elif e.detail == ErrorCode.LOGIN_BAD_CREDENTIALS:
            tip = "errors.badCredentials"
        else:
            tip = get_http_message(e.status_code)
        return response(e.status_code or -1, tip, desensitize(f"{e.status_code} {e.detail}"))
    return response(-1, desensitize(str(e)))
