from urllib.parse import urlparse

import httpx
import json
from fastapi import APIRouter, Depends, Response, Request

from api.conf import Config
from api.exceptions import ResourceNotFoundException, ArkoseForwardException, InvalidRequestException
from api.models.db import User
from api.response import handle_arkose_forward_exception
from api.sources import OpenaiWebChatManager
from api.users import current_active_user

config = Config()
router = APIRouter()
openai_web_manager = OpenaiWebChatManager()


def extract_origin(referer):
    parsed_url = urlparse(referer)

    scheme = parsed_url.scheme
    hostname = parsed_url.hostname
    port = parsed_url.port

    if port is None or port == 80 or port == 443:
        origin = f"{scheme}://{hostname}"
    else:
        origin = f"{scheme}://{hostname}:{port}"

    return origin


def modify_challenge_url_cdn(content: bytes):
    try:
        data = json.loads(content)
        if "challenge_url_cdn" in data:
            data["challenge_url_cdn"] = "/api/arkose/p" + data["challenge_url_cdn"]
            return json.dumps(data).encode()
    except json.JSONDecodeError:
        return content


def modify_fc_gt2_url(content: bytes):
    """
    这会导致 enforcement.x.html 中 script 标签的 integrity 校验失败
    """
    text = content.decode()
    if '"/fc/gt2/public_key/"' in text:
        text = text.replace('"/fc/gt2/public_key/"', '"/api/arkose/p/fc/gt2/public_key/"')
        return text.encode()
    return content


async def forward_arkose_request(request: Request, path: str, _user: User = Depends(current_active_user)):
    """
    TODO：/fc/a/?callback=
    """
    method = request.method
    headers = {
        "accept": request.headers.get("accept"),
        "content-type": request.headers.get("content-type"),
        "user-agent": request.headers.get("user-agent"),
    }

    referer = request.headers.get("referer")
    origin = request.headers.get("origin")

    if referer and "/arkose/p/" in referer:
        referer_path = referer.split("/arkose/p/", maxsplit=1)[1]
        referer = f"{config.openai_web.arkose_endpoint_base}{referer_path}"
        origin = extract_origin(referer)

    headers["referer"] = referer
    if origin:
        headers["origin"] = origin

    headers = {k: v for k, v in headers.items() if v is not None}
    data_bytes = await request.body()
    try:
        request_to_send = httpx.Request(method, f"{config.openai_web.arkose_endpoint_base}{path}", headers=headers,
                                        content=data_bytes, params=dict(request.query_params))
        async with httpx.AsyncClient() as client:
            resp = await client.send(request_to_send)
        resp.raise_for_status()
        headers = dict(resp.headers)
        headers.pop("content-encoding", None)
        headers.pop("transfer-encoding", None)
        headers.pop("content-length", None)

        resp_content_type = resp.headers.get("content-type")
        content = resp.content
        if resp_content_type and resp_content_type == "application/json":
            content = modify_challenge_url_cdn(resp.content)
        # elif resp_content_type and resp_content_type == "application/javascript":
        #     content = modify_fc_gt2_url(resp.content)
        return Response(content=content, headers=headers, status_code=200)
    except httpx.HTTPStatusError as e:
        e = ArkoseForwardException(code=e.response.status_code, message=e.response.text)
        return handle_arkose_forward_exception(e)


router.add_api_route("/arkose/p/{path:path}", forward_arkose_request, methods=["GET", "POST"])


@router.get("/arkose/info", tags=["arkose"])
async def get_arkose_info(_user: User = Depends(current_active_user)):
    return {
        "enabled": config.openai_web.enable_arkose_endpoint,
        # "url": "/v2/35536E1E-65B4-4D96-9D97-6ADB7EFF8147/api.js"
        "url": f"{config.openai_web.arkose_endpoint_base}35536E1E-65B4-4D96-9D97-6ADB7EFF8147/api.js"
    }
