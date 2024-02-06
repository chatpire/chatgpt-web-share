from datetime import datetime, timedelta

from fastapi import Depends, APIRouter
from fastapi_cache.decorator import cache

from api.models.db import User
from api.models.doc import AskLogDocument
from api.routers.conv import openai_web_manager
from api.routers.system import count_active_users_cached, count_active_users
from api.schemas.status_schemas import CommonStatusSchema
from api.users import current_active_user
from api.enums import OpenaiWebChatModels
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/status/common", tags=["status"], response_model=CommonStatusSchema)
@cache(expire=60)
async def get_server_status(_user: User = Depends(current_active_user)):
    result = await count_active_users()
    active_user_in_5m, active_user_in_1h, active_user_in_1d, queueing_count, _ = result
    pipeline = [
        {
            '$facet': {
                'not_found': [
                    {'$project': {'_id': None, 'total': {'$const': 0}}},
                    {'$limit': 1}
                ],
                'found': [
                    {'$match': {'time': {'$gte': datetime.utcnow() - timedelta(hours=3)}}},
                    {'$match': {
                        'meta.model': {'$in': [name for name in list(OpenaiWebChatModels) if name.startswith('gpt_4')]},
                        'meta.source': 'openai_web'}
                    },
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
    gpt4_count_in_3_hours = aggregate_result[0].get('total', 0)

    result = CommonStatusSchema(
        active_user_in_5m=active_user_in_5m,
        active_user_in_1h=active_user_in_1h,
        active_user_in_1d=active_user_in_1d,
        is_chatbot_busy=openai_web_manager.is_busy(),
        chatbot_waiting_count=queueing_count,
        gpt4_count_in_3_hours=gpt4_count_in_3_hours
    )
    return result
