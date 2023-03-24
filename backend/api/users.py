import contextlib
from datetime import datetime
from typing import Any

from fastapi.security import OAuth2PasswordRequestForm
from starlette.websockets import WebSocket

import api.exceptions
from api.config import config
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, models, IntegerIDMixin, InvalidID, schemas
from fastapi_users.authentication import CookieTransport, AuthenticationBackend
from fastapi_users.authentication import JWTStrategy

from api.database import get_user_db, get_async_session_context, get_user_db_context
from api.models import User

from sqlalchemy import select, Integer
from fastapi_users.models import UP
from utils.logger import get_logger

logger = get_logger(__name__)

# 使用 cookie + JWT
# 参考 https://fastapi-users.github.io/fastapi-users/10.2/configuration/full-example/

cookie_transport = CookieTransport(
    cookie_max_age=config.get("cookie_max_age", 86400),
    cookie_name="user_auth",
    cookie_httponly=False,
    cookie_secure=False,
)


# auth backend

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=config.get("jwt_secret"), lifetime_seconds=config.get("jwt_lifetime_seconds", 86400))


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# UserManager

SECRET = config.get("user_secret")


async def get_by_username(username: str) -> Optional[UP]:
    async with get_async_session_context() as session:
        user = await session.execute(select(User).filter(User.username == username))
        return user.scalar_one_or_none()


class UserManager(IntegerIDMixin, BaseUserManager[User, Integer]):
    async def create(self, user_create: schemas.UC, safe: bool = False, request: Optional[Request] = None) -> models.UP:
        # 检查用户名、手机、邮箱是否已经存在
        async with get_async_session_context() as session:
            if (await session.execute(select(User).filter(User.username == user_create.username))).scalar_one_or_none():
                raise api.exceptions.InvalidRequestException("Username already exists")
            if (await session.execute(select(User).filter(User.email == user_create.email))).scalar_one_or_none():
                raise api.exceptions.InvalidRequestException("Email already exists")
        return await super().create(user_create, safe, request)

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    def parse_id(self, value: Any) -> int:
        try:
            return int(value)
        except ValueError as e:
            raise InvalidID() from e

    async def authenticate(
            self, credentials: OAuth2PasswordRequestForm
    ) -> Optional[models.UP]:
        """
        Authenticate and return a user following an email and a password.

        Will automatically upgrade password hash if necessary.

        :param credentials: The user credentials.
        """
        user = await get_by_username(credentials.username)

        if user is None:
            # Run the hasher to mitigate timing attack
            # Inspired from Django: https://code.djangoproject.com/ticket/20760
            self.password_helper.hash(credentials.password)
            return None

        verified, updated_password_hash = self.password_helper.verify_and_update(
            credentials.password, user.hashed_password
        )
        if not verified:
            return None
        # Update password hash to a more robust one if needed
        if updated_password_hash is not None:
            await self.user_db.update(user, {"hashed_password": updated_password_hash})

        return user

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
            self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
            self, user: User, token: str, request: Optional[Request] = None
    ):
        print(
            f"Verification requested for user {user.id}. Verification token: {token}")


async def websocket_auth(websocket: WebSocket) -> User | None:
    user = None
    try:
        cookie = websocket._cookies[config.get("cookie_name", "user_auth")]
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    # user = await get_jwt_strategy().read_token(cookie, user_manager)
                    user, _ = await fastapi_users.authenticator._authenticate(
                        active=True,
                        user_manager=user_manager,
                        jwt=cookie,
                        strategy_jwt=get_jwt_strategy(),
                    )
    finally:
        return user


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)

# FastAPIUsers 实例，注意不要和 fastapi_users 包混淆
fastapi_users = FastAPIUsers[User, Integer](get_user_manager, [auth_backend])

__current_active_user = fastapi_users.current_user(active=True)


async def current_active_user(user: User = Depends(__current_active_user)):
    current_time = datetime.utcnow()
    user.active_time = current_time
    try:
        async with get_async_session_context() as session:
            user_update = await session.get(User, user.id)
            user_update.active_time = current_time
            session.add(user_update)
            await session.commit()
    except Exception as e:
        logger.warning(e)
    finally:
        return user


current_super_user = fastapi_users.current_user(active=True, superuser=True)
