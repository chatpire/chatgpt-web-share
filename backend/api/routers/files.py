import uuid

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from starlette.responses import FileResponse

from api.conf import Config
from api.database.sqlalchemy import get_async_session_context
from api.exceptions import InvalidRequestException, ResourceNotFoundException, AuthorityDenyException
from api.file_provider import FileProvider
from api.models.db import User
from api.schemas.file_schemas import UploadedFileInfoSchema
from api.sources import OpenaiWebChatManager
from api.users import current_active_user

config = Config()
router = APIRouter()
file_provider = FileProvider()
openai_web_manager = OpenaiWebChatManager()


@router.post("/files/upload/", tags=["files"], response_model=UploadedFileInfoSchema)
async def upload_file(file: UploadFile = File(...), user: User = Depends(current_active_user)):
    if file.size > config.data.max_upload_size:
        raise InvalidRequestException(f"File too large! Max size: {config.data.max_upload_size}")

    async with get_async_session_context() as session:
        file_info = await file_provider.save_file(file, user.id, session)

    return UploadedFileInfoSchema.from_orm(file_info)


@router.get("/files/download/{file_id}", tags=["files"])
async def download_file(file_id: uuid.UUID):
    async with get_async_session_context() as session:
        file_info = await file_provider.get_file_info(file_id, session)
    if not file_info:
        raise ResourceNotFoundException(f"No such file: {file_id}")

    file_path = file_provider.get_absolute_path(file_info.storage_path)
    if not file_path.exists():
        raise ResourceNotFoundException(
            f"File {file_info.original_filename} ({file_id}) not exists. This may be caused by file cleanup.")

    return FileResponse(file_path, filename=file_info.original_filename)


@router.post("/files/upload-to-openai/{file_id}", tags=["files"], response_model=UploadedFileInfoSchema)
async def upload_file_to_openai_web(file_id: uuid.UUID, user: User = Depends(current_active_user)):
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
        await session.update(file_info)
        await session.commit()

        return UploadedFileInfoSchema.from_orm(file_info)

