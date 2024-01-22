from __future__ import annotations

import http
import logging
import os
import sys
import time
from typing import TypedDict

from asgiref.typing import ASGI3Application, ASGIReceiveCallable, ASGISendCallable
from asgiref.typing import ASGISendEvent, HTTPScope

from .utils import get_client_addr, get_path_with_query_string


class AccessInfo(TypedDict, total=False):
    response: ASGISendEvent
    start_time: float
    end_time: float


class AccessLoggerMiddleware:
    DEFAULT_FORMAT = '%(client_addr)s - "%(request_line)s" %(status_code)s'

    def __init__(
        self,
        app: ASGI3Application,
        format: str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.app = app
        self.format = format or self.DEFAULT_FORMAT
        if logger is None:
            self.logger = logging.getLogger("access")
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
        else:
            self.logger = logger

    async def __call__(
        self, scope: HTTPScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)  # pragma: no cover

        info = AccessInfo(response={})

        async def inner_send(message: ASGISendEvent) -> None:
            if message["type"] == "http.response.start":
                info["response"] = message
            await send(message)

        try:
            info["start_time"] = time.time()
            await self.app(scope, receive, inner_send)
        except Exception as exc:
            info["response"]["status"] = 500
            raise exc
        finally:
            info["end_time"] = time.time()
            self.log(scope, info)

    def log(self, scope: HTTPScope, info: AccessInfo) -> None:
        self.logger.info(self.format, AccessLogAtoms(scope, info))


class AccessLogAtoms(dict):
    def __init__(self, scope: HTTPScope, info: AccessInfo) -> None:
        for name, value in scope["headers"]:
            self[f"{{{name.decode('latin1').lower()}}}i"] = value.decode("latin1")
        for name, value in info["response"].get("headers", []):
            self[f"{{{name.decode('latin1').lower()}}}o"] = value.decode("latin1")
        for name, value in os.environ.items():
            self[f"{{{name.lower()!r}}}e"] = value

        protocol = f"HTTP/{scope['http_version']}"

        status = info["response"].get("status", None)
        try:
            if status:
                status_phrase = http.HTTPStatus(status).phrase
            else:
                status_phrase = "-"
        except ValueError:
            status_phrase = "-"

        path = scope["root_path"] + scope["path"]
        full_path = get_path_with_query_string(scope)
        request_line = f"{scope['method']} {path} {protocol}"
        full_request_line = f"{scope['method']} {full_path} {protocol}"

        request_time = info["end_time"] - info["start_time"]
        client_addr = get_client_addr(scope)
        self.update(
            {
                "h": client_addr,
                "client_addr": client_addr,
                "l": "-",
                "u": "-",  # Not available on ASGI.
                "t": time.strftime("[%d/%b/%Y:%H:%M:%S %z]"),
                "r": request_line,
                "request_line": full_request_line,
                "R": full_request_line,
                "m": scope["method"],
                "U": scope["path"],
                "q": scope["query_string"].decode(),
                "H": protocol,
                "s": status,
                "status_code": f"{status} {status_phrase}",
                "st": status_phrase,
                "B": self["{Content-Length}o"],
                "b": self.get("{Content-Length}o", "-"),
                "f": self["{Referer}i"],
                "a": self["{User-Agent}i"],
                "T": str(round(request_time)),
                "M": str(round(request_time * 1_000)),
                "D": str(round(request_time * 1_000_000)),
                "L": f"{request_time:.6f}",
                "p": f"<{os.getpid()}>",
            }
        )

    def __getitem__(self, key: str) -> str:
        try:
            if key.startswith("{"):
                return super().__getitem__(key.lower())
            else:
                return super().__getitem__(key)
        except KeyError:
            return "-"