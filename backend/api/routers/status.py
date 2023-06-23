from datetime import datetime, timedelta

from fastapi import Depends, APIRouter

from api.models.db import User
from api.models.doc import AskLogDocument
from api.routers.conv import openai_web_manager
from api.routers.system import check_users
from api.schemas.status_schemas import CommonStatusSchema
from api.users import current_active_user
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/status/common", tags=["status"], response_model=CommonStatusSchema)
async def get_server_status(_user: User = Depends(current_active_user)):
    """普通用户获取服务器状态"""
    refresh_cache = _user.is_superuser
    active_user_in_5m, active_user_in_1h, active_user_in_1d, queueing_count, _ = await check_users(refresh_cache)
    pipeline = [
        {
            '$facet': {
                'not_found': [
                    {'$project': {'_id': None, 'total': {'$const': 0}}},
                    {'$limit': 1}
                ],
                'found': [
                    {'$match': {'time': {'$gte': datetime.utcnow() - timedelta(hours=3)}}},
                    {'$count': 'total'}
                ]
            }
        },
        {
            '$replaceRoot': {
                'newRoot': {
                    '$mergeObjects': [
                        {'$arrayElemAt': ['$not_found', 0]},
                        {'$arrayElemAt': ['$found', 0]}
                    ]
                }
            }
        }
    ]
    aggregate_result = await AskLogDocument.aggregate(pipeline).to_list(length=1)
    gpt4_count_in_3_hours = aggregate_result[0].get('total')

    result = CommonStatusSchema(
        active_user_in_5m=active_user_in_5m,
        active_user_in_1h=active_user_in_1h,
        active_user_in_1d=active_user_in_1d,
        is_chatbot_busy=openai_web_manager.is_busy(),
        chatbot_waiting_count=queueing_count,
        gpt4_count_in_3_hours=gpt4_count_in_3_hours
    )
    return result
