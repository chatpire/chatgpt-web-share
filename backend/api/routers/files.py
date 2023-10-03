import uuid
from datetime import datetime, timezone
from mimetypes import guess_type

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi_cache.decorator import cache
from starlette.responses import FileResponse

from api.conf import Config
from api.database.sqlalchemy import get_async_session_context
from api.enums.options import OpenaiWebFileUploadStrategyOption
from api.exceptions import InvalidRequestException, ResourceNotFoundException, AuthorityDenyException
from api.file_provider import FileProvider
from api.models.db import User, UploadedFileInfo
from api.models.json import UploadedFileOpenaiWebInfo
from api.schemas.file_schemas import UploadedFileInfoSchema, StartUploadResponseSchema
from api.schemas.openai_schemas import OpenaiChatFileUploadInfo
from api.sources import OpenaiWebChatManager
from api.users import current_active_user

config = Config()
router = APIRouter()
file_provider = FileProvider()
openai_web_manager = OpenaiWebChatManager()


@router.get("/files/{file_id}/download-url", tags=["conversation"], response_model=str)
@cache(expire=60 * 60 * 24)
async def get_file_download_url(file_id: str):
    """
    file_id: OpenAI 分配的 id，以 file- 开头
    """
    url = await openai_web_manager.get_file_download_url(file_id)
    return url


@router.post("/files/local/upload", tags=["files"], response_model=UploadedFileInfoSchema)
async def upload_file_to_local(file: UploadFile = File(...), user: User = Depends(current_active_user)):
    """
    上传文件到服务器。文件将被保存在服务器上，返回文件信息。
    仅当需要在服务器留存上传的文件时才使用.
    """
    if config.openai_web.file_upload_strategy in [OpenaiWebFileUploadStrategyOption.browser_upload_only,
                                                  OpenaiWebFileUploadStrategyOption.disable_upload]:
        raise InvalidRequestException(f"File upload disabled")
    if file.size > config.data.max_file_upload_size:
        raise InvalidRequestException(f"File too large! Max size: {config.data.max_file_upload_size}")

    async with get_async_session_context() as session:
        file_info = await file_provider.save_file(file, user.id, session)

    return UploadedFileInfoSchema.from_orm(file_info)


@router.get("/files/local/download/{file_id}", tags=["files"])
async def download_file_from_local(file_id: uuid.UUID, user: User = Depends(current_active_user)):
    async with get_async_session_context() as session:
        file_info = await file_provider.get_file_info(file_id, session)
    if not file_info:
        raise ResourceNotFoundException(f"No such file: {file_id}")
    if not user.is_superuser and file_info.uploader_id != user.id:
        raise AuthorityDenyException(f"File {file_id} not uploaded by you")

    file_path = file_provider.get_absolute_path(file_info.storage_path)
    if not file_path.exists():
        raise ResourceNotFoundException(
            f"File {file_info.original_filename} ({file_id}) not exists. This may be caused by file cleanup.")

    return FileResponse(file_path, filename=file_info.original_filename)


@router.post("/files/openai-web/upload-start", tags=["files"], response_model=StartUploadResponseSchema)
async def start_upload_to_openai(upload_info: OpenaiChatFileUploadInfo, user: User = Depends(current_active_user)):
    """
    要上传文件到 OpenAI Web，前端需要先调用此接口.
    1. 若最终上传方法是前端直接上传 (Browser -> Azure Blob)，则获取上传地址并记录文件信息，响应中 upload_file_info 不为空
    2. 否则的话就是服务端中转上传（Browser -> Local -> Azure Blob，此时响应中 upload_file_info 为空，前端应当:
        a. 先调用 upload_file_to_local 接口上传文件到服务器，拿到文件的 uuid
        b. 再调用 upload_local_file_to_openai_web 接口，通知服务器上传文件到 OpenAI Web
    """
    file_size_exceed = upload_info.file_size > config.data.max_file_upload_size
    if upload_info.use_case != "ace_upload":
        raise InvalidRequestException(f"Invalid use case: {upload_info.use_case}")
    if config.openai_web.file_upload_strategy == OpenaiWebFileUploadStrategyOption.server_upload_only and file_size_exceed:
        raise InvalidRequestException(f"File too large! Max size: {config.data.max_file_upload_size}")
    if config.openai_web.file_upload_strategy == OpenaiWebFileUploadStrategyOption.disable_upload:
        raise InvalidRequestException(f"File upload disabled")

    file_info = None

    # 浏览器直接上传
    if config.openai_web.file_upload_strategy == OpenaiWebFileUploadStrategyOption.browser_upload_only or \
            config.openai_web.file_upload_strategy == OpenaiWebFileUploadStrategyOption.browser_upload_when_file_size_exceed and file_size_exceed:
        response = await openai_web_manager.get_file_upload_url(upload_info)
        file_info = UploadedFileInfoSchema(
            id=uuid.uuid4(),
            original_filename=upload_info.file_name,
            size=upload_info.file_size,
            content_type=guess_type(upload_info.file_name)[0],
            storage_path=None,
            uploader_id=user.id,
            upload_time=datetime.now().astimezone(tz=timezone.utc),
            openai_web_info=UploadedFileOpenaiWebInfo(
                file_id=response.file_id,
                upload_url=response.upload_url,
                download_url=None
            )
        )
        async with get_async_session_context() as session:
            session.add(UploadedFileInfo(**file_info.dict()))
            await session.commit()

    return StartUploadResponseSchema(
        strategy=config.openai_web.file_upload_strategy,
        file_max_size=config.data.max_file_upload_size,
        upload_file_info=file_info
    )


@router.post("/files/openai-web/upload-complete/{file_id}", tags=["files"], response_model=UploadedFileInfoSchema)
async def complete_upload_to_openai(file_id: uuid.UUID, user: User = Depends(current_active_user)):
    async with get_async_session_context() as session:
        file_info = await file_provider.get_file_info(file_id, session)
        if not file_info:
            raise ResourceNotFoundException(f"No such file: {file_id}")
        if file_info.openai_web_info is None or file_info.openai_web_info.file_id is None:
            raise InvalidRequestException(f"File {file_id} not uploaded to OpenAI Web")
        if file_info.openai_web_info.download_url is not None:
            raise InvalidRequestException(f"File {file_id} already uploaded to server")
        if not user.is_superuser and file_info.uploader_id != user.id:
            raise AuthorityDenyException(f"File {file_id} not uploaded by you")
        if file_info.storage_path is not None:
            raise InvalidRequestException(f"File {file_id} already uploaded to server")

        file_info_schema = UploadedFileInfoSchema.from_orm(file_info)
        openai_web_info = file_info_schema.openai_web_info
        download_url = await openai_web_manager.check_file_uploaded(file_info.openai_web_info.file_id)
        openai_web_info.download_url = download_url
        openai_web_info.upload_url = None
        file_info.openai_web_info = openai_web_info

        session.add(file_info)
        await session.commit()

        return UploadedFileInfoSchema.from_orm(file_info)


@router.post("/files/local/upload-to-openai-web/{file_id}", tags=["files"], response_model=UploadedFileInfoSchema)
async def upload_local_file_to_openai_web(file_id: uuid.UUID, user: User = Depends(current_active_user)):
    """
    将服务器上已有的文件上传到 OpenAI Web（Azure blob）
    """
    async with get_async_session_context() as session:
        file_info = await file_provider.get_file_info(file_id, session)
        if not file_info:
            raise ResourceNotFoundException(f"No such file: {file_id}")
        if file_info.openai_web_info is not None:
            raise InvalidRequestException(f"File {file_id} already uploaded to OpenAI Web")
        if not user.is_superuser and file_info.uploader_id != user.id:
            raise AuthorityDenyException(f"File {file_id} not uploaded by you")

        openai_web_file_info = await openai_web_manager.upload_file_in_server(file_info)
        file_info.openai_web_info = openai_web_file_info
        await session.commit()

        return UploadedFileInfoSchema.from_orm(file_info)
