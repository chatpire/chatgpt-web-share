from api.database import get_user_db_context, get_async_session_context
from api.models import UserSetting
from api.schema import UserCreate
from api.users import get_user_manager_context
from utils.logger import get_logger

logger = get_logger(__name__)


async def create_user(user_create: UserCreate, safe=True, request=None):
    async with get_async_session_context() as session:
        user_setting = UserSetting(**user_create.setting.dict())
        user_create.setting = user_setting
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                user = await user_manager.create(user_create, safe=safe, request=request)
                logger.info(f"User created: {user.username}")

        user_setting.user_id = user.id
        session.add(user_setting)
        await session.commit()
        await session.refresh(user)
        return user
