from fastapi import APIRouter, Depends
from sqlalchemy.future import select
from starlette.requests import Request

from api.database import get_async_session_context, get_user_db_context
from api.exceptions import UserNotExistException
from api.models.db import User,InviteCode
from api.schemas import UserRead, UserUpdate, UserCreate, UserUpdateAdmin, UserReadAdmin, UserSettingSchema, InviteCodeCreate, InviteCodeRequest
from api.users import auth_backend, fastapi_users, current_active_user, get_user_manager_context, current_super_user
import uuid
from datetime import datetime, timedelta, timezone

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"]
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"]
)
# router.include_router(
#     fastapi_users.get_reset_password_router(),
#     prefix="/auth",
#     tags=["auth"],
# )

@router.post("/auth/adminregister", response_model=UserReadAdmin, tags=["auth"])
async def register(
        request: Request,
        user_create: UserCreate,
        _user: User = Depends(current_super_user),
):
    """注册时不能指定setting，使用默认setting"""
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                user = await user_manager.create(user_create, safe=False, request=request,SuperUsername=_user.nickname)
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
    

@router.post("/user/createcode", response_model=InviteCodeCreate, tags=["user"])
async def create_user_invite_code(request: InviteCodeRequest, _user: User = Depends(current_super_user)):
    uuid_str = str(uuid.uuid4())
    now_utc_date = datetime.now(timezone.utc)
    async with get_async_session_context() as session:
        uuid_res = await session.get(InviteCode, uuid_str)
        while uuid_res is not None:
            uuid_str = str(uuid.uuid4())
            uuid_res = await session.get(InviteCode, uuid_str)
        if request.expiration_date == 0:
            created_code=InviteCode(code=uuid_str,invite_name=_user.nickname,expire_time=None)
        else:
            created_code=InviteCode(code=uuid_str,invite_name=_user.nickname,expire_time=now_utc_date+timedelta(days=request.expiration_date))
        session.add(created_code)
        await session.commit()
        return created_code
        