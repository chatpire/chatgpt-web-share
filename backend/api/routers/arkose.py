import httpx
from fastapi import APIRouter, Depends, Response

from api.conf import Config
from api.exceptions import ResourceNotFoundException, ArkoseForwardException
from api.models.db import User
from api.sources import OpenaiWebChatManager
from api.users import current_active_user

config = Config()
router = APIRouter()
openai_web_manager = OpenaiWebChatManager()


@router.get("/arkose/v2/{path:path}", tags=["arkose"])
async def forward_arkose_request(path: str, _user: User = Depends(current_active_user)):
    """
    TODO 经过转发，arkose 会报错 "API_REQUEST_ERROR"
    """
    try:
        resp = await openai_web_manager.session.get(f"{config.openai_web.arkose_endpoint_base}{path}")
        resp.raise_for_status()
        headers = dict(resp.headers)
        media_type = resp.headers.get("content-type")
        headers.pop("content-length", None)
        headers.pop("content-encoding", None)
        return Response(content=resp.content, media_type=media_type, headers=headers)
    except httpx.HTTPStatusError as e:
        raise ArkoseForwardException(code=e.response.status_code, message=e.response.text)
    except Exception as e:
        return ArkoseForwardException(code=500, message=str(e))


@router.get("/arkose/info", tags=["arkose"])
async def get_arkose_info(_user: User = Depends(current_active_user)):
    return {
        "enabled": config.openai_web.enable_arkose_endpoint,
        "url": f"{config.openai_web.arkose_endpoint_base}35536E1E-65B4-4D96-9D97-6ADB7EFF8147/api.js"
    }
