from sqlalchemy.future import select
from sqlalchemy import insert, update, delete
from sqlalchemy.orm import joinedload

from api.models import Api, User, UserApi
from api.response import response
from api.schema import ApiRead, ApiUpdate, ApiCreate, UserApiCreate
from api.users import current_active_user, current_super_user
from api.database import get_async_session_context, get_user_db_context
import json
import openai
import requests

from fastapi import APIRouter, Depends
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/system/api", tags=["api"])
async def get_all_apis(_user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        r = await session.execute(select(Api))
        results = r.scalars().all()
        return results
    
@router.post("/system/api", tags=["api"])
async def create_api(apiInfo: ApiCreate, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        r = await session.execute(select(Api).where(Api.key == apiInfo.key))
        if r.scalars().first():
            return response(400, "errors.apiNameAlreadyExist")
        api = Api(**apiInfo.dict())
        if apiInfo.type == "openai":
            openai.api_key = apiInfo.key
            try:
                models = openai.Model.list()
            except openai.error.AuthenticationError:
                return response(400, "errors.apiKeyInvalid")
            model_info = {vo['id']: vo['id']  for vo in models.data if 'gpt' in vo['id']}
        elif apiInfo.type == "azure":
            url = f"{api.endpoint}/openai/deployments?api-version=2023-03-15-preview"
            headers = {
                'api-key': apiInfo.key
            }

            res = requests.request("GET", url, headers=headers)
            model_info = {vo['model']: vo['id'] for vo in res.json()['data']}


        api.models = model_info
        
        session.add(api)
        await session.commit()
        logger.debug(r)
        return response(200, "success", result=api)

@router.delete("/system/api/{api_id}", tags=["api"])
async def delete_api(api_id: int, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        r = await session.execute(select(Api).where(Api.id == api_id))
        api = r.scalars().first()
        if not api:
            return response(400, "errors.apiNotExist")
        await session.execute(delete(Api).where(Api.id == api_id))
        await session.commit()
        return response(200, "success")
    
@router.get("/system/user/api/", tags=["user_api"])
async def get_user_apis(user_id: int = None, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        query = select(UserApi)
        if user_id:
            query = query.where(UserApi.user_id == user_id)
        r = await session.execute(query.options(joinedload(UserApi.api)))
        apis = r.scalars().all()
        return response(200, "success", result=apis)
    
@router.post("/system/user/api/", tags=["user_api"])
async def create_user_apis(user_api: UserApiCreate, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        r = await session.execute(select(UserApi)
                                  .where(UserApi.user_id == user_api.user_id, 
                                         UserApi.api_id == user_api.api_id))
        if r.scalars().first():
            return response(400, "errors.apiAlreadyExist")
        user = await session.execute(select(User).where(User.id == user_api.user_id))
        if not user.scalars().first():
            return response(400, "errors.userNotExist")
        
        api = await session.execute(select(Api).where(Api.id == user_api.api_id))
        api = api.scalars().first()
        if not api:
            return response(400, "errors.apiNotExist")
        
        support_models = api.models.keys()
        for model in user_api.models:
            if model not in support_models:
                return response(400, "errors.modelNotExist")
        
        dto = UserApi(**user_api.dict())
        session.add(dto)
        await session.commit()
        return response(200, "success", result=dto)

@router.delete("/system/user/api/{user_api_id}", tags=["user_api"])
async def delete_user_apis(user_api_id: int, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        r = await session.execute(select(UserApi).where(UserApi.id == user_api_id))
        user_api = r.scalars().first()
        if not user_api:
            return response(400, "errors.apiNotExist")
        await session.execute(delete(UserApi).where(UserApi.id == user_api_id))
        await session.commit()
        return response(200, "success")
    
@router.patch("/system/user/api/{user_api_id}", tags=["user_api"])
async def update_user_apis(user_api_id: int, user_api: UserApiCreate, _user: User = Depends(current_super_user)):
    async with get_async_session_context() as session:
        r = await session.execute(select(UserApi).where(UserApi.id == user_api_id))
        if not r.scalars().first():
            return response(400, "errors.apiNotExist")
        user = await session.execute(select(User).where(User.id == user_api.user_id))
        if not user.scalars().first():
            return response(400, "errors.userNotExist")
        
        api = await session.execute(select(Api).where(Api.id == user_api.api_id))
        api = api.scalars().first()
        if not api:
            return response(400, "errors.apiNotExist")
        
        support_models = api.models.keys()
        for model in user_api.models:
            if model not in support_models:
                return response(400, "errors.modelNotExist")
        
        await session.execute(update(UserApi).where(UserApi.id == user_api_id).values(**user_api.dict()))
        await session.commit()
        return response(200, "success", result=user_api)
    
@router.get("/api/user/models/", tags=["user_api"])
async def get_current_user_support_models(_user: User = Depends(current_active_user)):
    async with get_async_session_context() as session:
        user_id = _user.id
        logger.info(user_id)
        r = await session.execute(select(UserApi).where(UserApi.user_id == user_id).options(joinedload(UserApi.api)))
        # get raw sql
        data = r.scalars().all()
        models = []
        for vo in data:
            for model in vo.models:
                logger.info(model)
                key = vo.api.type + '-' + model
                if key not in models:
                    models.append(vo.api.type + '-' + model)
        return response(200, "success", result=models)