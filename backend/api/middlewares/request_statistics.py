import json
import re
import time
from typing import Optional

from asgiref.typing import ASGI3Application, HTTPScope, ASGIReceiveCallable, ASGISendCallable
from fastapi.routing import APIRoute

import api.globals as g
from api.models.doc import RequestLogDocument, RequestLogMeta

from utils.logger import get_logger

logger = get_logger(__name__)


class StatisticsMiddleware:
    """
    统计请求的中间件
    """
    def __init__(
            self,
            app: ASGI3Application,
            filter_keywords: Optional[list[str]] = None,
    ) -> None:
        self.app = app
        self.filter_keywords = filter_keywords

    async def __call__(
            self, scope: HTTPScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        if scope["type"] != "http" and scope["type"] != "websocket":
            return await self.app(scope, receive, send)

        raw_status_code = None
        body_code = None

        async def send_with_inspecting_body(message):
            """用于记录状态码"""
            nonlocal raw_status_code, body_code
            if message["type"] == "http.response.start":
                raw_status_code = message.get("status", None)
            elif message["type"] == "http.response.body":
                body = message.get("body", None)  # byte string
                if body is not None:
                    body = body.decode("utf-8")
                    try:
                        body = json.loads(body)
                        body_code = body.get("code", None)
                    except json.JSONDecodeError:
                        pass

            await send(message)

        start_time = time.time()
        try:
            await self.app(scope, receive, send_with_inspecting_body)
        except Exception as exc:
            raise exc
        finally:
            end_time = time.time()

            route: APIRoute | None = scope.get("route", None)
            if route is None:
                return

            if self.filter_keywords:
                for keyword in self.filter_keywords:
                    if route.path.find(keyword) != -1:
                        return

            user_id = None
            if "auth_user" in scope:
                user = scope["auth_user"]
                user_id = user.id

            if scope.get("method"):
                method = scope["method"]
            elif scope["type"] == "websocket":
                method = "WEBSOCKET"
            else:
                logger.debug(f"Unknown method for scope type: {scope['type']}")
                return

            elapsed_ms = end_time - start_time
            elapsed_ms = round(elapsed_ms * 1000, 2)

            await RequestLogDocument(
                meta=RequestLogMeta(route_path=route.path, method=method),
                user_id=user_id,
                elapsed_ms=elapsed_ms,
                status=body_code or raw_status_code or scope.get("ask_websocket_close_code", None)
            ).create()
