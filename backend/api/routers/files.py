import uuid

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from starlette.responses import FileResponse

from api.conf import Config
from api.database import get_async_session_context
from api.exceptions import InvalidRequestException
from api.file_provider import FileProvider
from api.models.db import User
from api.schemas.file_schemas import UploadedFileSchema
from api.users import current_active_user

config = Config()
router = APIRouter()
file_provider = FileProvider()


@router.post("/upload/", response_model=UploadedFileSchema)
async def upload_file(file: UploadFile = File(...), user: User = Depends(current_active_user)):
    if file.size > config.data.max_upload_size:
        raise InvalidRequestException(f"File too large! Max size: {config.data.max_upload_size}")

    async with get_async_session_context() as session:
        file_info = await file_provider.save_file(file, user.id, session)
    return file_info


@router.get("/download/{file_uuid}/")
async def download_file(file_uuid: uuid.UUID):
    async with get_async_session_context() as session:
        file_path = await file_provider.get_file_path(file_uuid, session)
    if not file_path:
        raise FileNotFoundError(f"file {file_uuid} not found")
    if not file_path.exists():
        raise FileNotFoundError(f"file {file_uuid} not exists")

    return FileResponse(file_path, filename=file_path.name)
