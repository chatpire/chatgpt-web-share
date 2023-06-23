from typing import Tuple

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager
from fastapi_users.authentication import Strategy
from sqlalchemy.future import select
from starlette.requests import Request

from api.database import get_async_session_context, get_user_db_context
from api.exceptions import UserNotExistException, AuthenticationFailedException
from api.models.db import User
from api.response import response
from api.schemas import UserRead, UserUpdate, UserCreate, UserUpdateAdmin, UserReadAdmin, UserSettingSchema
from api.users import auth_backend, fastapi_users, current_active_user, get_user_manager_context, current_super_user, \
    get_user_manager, UserManager

router = APIRouter()


# router.include_router(
#     fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"]
# )


@router.post("/auth/login", name=f"auth:{auth_backend.name}.login")
async def login(
        request: Request,
        credentials: OAuth2PasswordRequestForm = Depends(),
        user_manager: UserManager = Depends(get_user_manager),
        strategy: Strategy[User, int] = Depends(auth_backend.get_strategy),
):
    user = await user_manager.authenticate(credentials)

    if user is None or not user.is_active:
        raise AuthenticationFailedException()
    # if requires_verification and not user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
    #     )
    resp = await auth_backend.login(strategy, user)
    return response(200, headers=resp.headers)


get_current_user_token = fastapi_users.authenticator.current_user_token(
    active=True, verified=False
)


@router.post("/auth/logout", name=f"auth:{auth_backend.name}.logout")
async def logout(
        user_token: Tuple[User, str] = Depends(get_current_user_token),
        strategy: Strategy[User, int] = Depends(auth_backend.get_strategy),
):
    user, token = user_token
    resp = await auth_backend.logout(strategy, user, token)
    return response(200, headers=resp.headers)


@router.post("/auth/register", response_model=UserReadAdmin, tags=["auth"])
async def register(
        request: Request,
        user_create: UserCreate,
        _user: User = Depends(current_super_user),
):
    """注册时不能指定setting，使用默认setting"""
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                user = await user_manager.create(user_create, safe=False, request=request)
                return UserReadAdmin.from_orm(user)


@router.get("/user", tags=["user"])
async def get_all_users(_user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        r = await session.execute(select(User))
        results = r.scalars().all()
        return results


# router.include_router(
#     fastapi_users.get_users_router(UserRead, UserUpdate),
#     prefix="/user",
#     tags=["user"],
# )


@router.get("/user/me", response_model=UserRead, tags=["user"])
async def get_me(user: User = Depends(current_active_user)):
    return UserRead.from_orm(user)


@router.patch("/user/me", response_model=UserRead, tags=["user"])
async def update_me(
        request: Request,
        user_update: UserUpdate,  # type: ignore
        _user: User = Depends(current_active_user),
):
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                user = await session.get(User, _user.id)
                user = await user_manager.update(
                    user_update, user, safe=True, request=request
                )
                return UserRead.from_orm(user)


@router.get("/user/{user_id}", response_model=UserReadAdmin, tags=["user"])
async def admin_get_user(user_id: int, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        if user is None:
            raise UserNotExistException()
        result = UserRead.from_orm(user)
        return result


@router.patch("/user/{user_id}", tags=["user"])
async def admin_update_user(user_update_admin: UserUpdateAdmin, request: Request,
                            user_id: int, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                user = await session.get(User, user_id)
                user = await user_manager.update(
                    user_update_admin, user, safe=False, request=request
                )
                return UserReadAdmin.from_orm(user)


@router.delete("/user/{user_id}", tags=["user"])
async def admin_delete_user(user_id: int, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        await session.delete(user)
        await session.commit()
        return None


@router.patch("/user/{user_id}/setting", response_model=UserReadAdmin, tags=["user"])
async def admin_update_user_setting(user_id: int, user_setting: UserSettingSchema,
                                    _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        if user is None:
            raise UserNotExistException()
        for key, value in user_setting.dict(exclude={'id', 'user_id'}).items():
            setattr(user.setting, key, value)
        await session.commit()
        await session.refresh(user)
        return UserReadAdmin.from_orm(user)
