import re
import time
from typing import Optional

from asgiref.typing import ASGI3Application, HTTPScope, ASGIReceiveCallable, ASGISendCallable
import api.globals as g
from api.models.doc import RequestStatDocument, RequestStatMeta

from utils.logger import get_logger

logger = get_logger(__name__)


class StatisticsMiddleware:
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

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            raise exc
        finally:
            route = scope["route"]
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

            await RequestStatDocument(
                meta=RequestStatMeta(route_path=route.path, method=method),
                user_id=user_id,
            ).create()
