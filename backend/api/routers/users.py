from typing import Union

from sqlalchemy.future import select
from starlette.requests import Request
from pydantic import BaseModel
from api.database import get_async_session_context, get_user_db_context
from api.exceptions import AuthorityDenyException, InvalidParamsException, UserNotExistException
from api.models import User, UserSetting
from api.response import response
from api.schema import UserRead, UserUpdate, UserCreate, UserUpdateAdmin, UserReadAdmin, UserSettingSchema
from api.users import auth_backend, fastapi_users, current_active_user, get_user_manager_context, current_super_user
from utils.admin import create_user
from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import exceptions

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"]
)


# router.include_router(
#     fastapi_users.get_reset_password_router(),
#     prefix="/auth",
#     tags=["auth"],
# )

@router.post("/auth/register", tags=["auth"])
async def register(
        request: Request,
        user_create: UserCreate,
        _user: User = Depends(current_super_user),
):
    created_user = await create_user(
        user_create, safe=False, request=request
    )

    return UserRead.from_orm(created_user)


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
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                user = await session.get(User, user_id)
                await user_manager.delete(user)
                return None


@router.patch("/user/{user_id}/setting", response_model=UserReadAdmin, tags=["user"])
async def admin_update_user_setting(user_id: int, user_setting: UserSettingSchema,
                                    _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        user = await session.get(User, user_id)
        if user is None:
            raise UserNotExistException()
        for key, value in user_setting.dict(exclude_unset=True, exclude={'id', 'user_id'}).items():
            setattr(user.setting, key, value)
        await session.commit()
        await session.refresh(user)
        return UserReadAdmin.from_orm(user)
