import time
from asgiref.typing import ASGI3Application, HTTPScope, ASGIReceiveCallable, ASGISendCallable
import api.globals as g

from utils.logger import get_logger

logger = get_logger(__name__)


class StatisticsMiddleware:
    """
    Middleware for request_statistics.
    filter_paths: List of paths keywords to filter.
    """

    def __init__(
            self,
            app: ASGI3Application
    ) -> None:
        self.app = app

    async def __call__(
            self, scope: HTTPScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        if scope["type"] != "http" and scope["type"] != "websocket":
            return await self.app(scope, receive, send)

        start_time = time.time()
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            raise exc
        finally:
            end_time = time.time()

            g.request_log_counter.count()
            # logger.debug(g.request_log_counter)
            # path = scope["root_path"] + scope["path"]

            if scope["type"] == "websocket":
                user_name = scope["auth_user"].username or None
                g.ask_log_queue.enqueue((user_name, end_time - start_time))
                # logger.debug(g.ask_log_queue)
