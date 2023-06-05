from fastapi import Depends, APIRouter

from api.models.db import User
from api.routers.conv import openai_web_manager
from api.routers.system import check_users
from api.schemas import ServerStatusSchema
from api.users import current_active_user

router = APIRouter()


@router.get("/status", tags=["status"], response_model=ServerStatusSchema)
async def get_server_status(_user: User = Depends(current_active_user)):
    """普通用户获取服务器状态"""
    refresh_cache = _user.is_superuser
    active_user_in_5m, active_user_in_1h, active_user_in_1d, queueing_count, _ = await check_users(refresh_cache)
    result = ServerStatusSchema(
        active_user_in_5m=active_user_in_5m,
        active_user_in_1h=active_user_in_1h,
        active_user_in_1d=active_user_in_1d,
        is_chatbot_busy=openai_web_manager.is_busy(),
        chatbot_waiting_count=queueing_count
    )
    return result
