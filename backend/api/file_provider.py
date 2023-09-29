import os
import shutil
import uuid
from datetime import datetime, timezone
from mimetypes import guess_type
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.conf import Config
from api.models.db import UploadedFileInfo

config = Config()


class FileProvider:
    def __init__(self, storage_dir: Path = None, max_size: int = None):
        self.max_size = max_size or config.data.max_file_upload_size
        self.storage_dir = storage_dir or (Path(config.data.data_dir) / "uploads")
        if not self.storage_dir.exists():
            self.storage_dir.mkdir()

    async def save_file(self, file: UploadFile, user_id: int, session: AsyncSession):
        file_name = f"{uuid.uuid4()}.dat"
        file_dir_path = self.storage_dir / f"{user_id}"
        file_path = file_dir_path / file_name

        if not file_dir_path.exists():
            file_dir_path.mkdir(parents=True)

        async with aiofiles.open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)  # read by 1MB chunk
                if not chunk:
                    break
                await buffer.write(chunk)

        file_info = UploadedFileInfo(
            original_filename=file.filename,
            size=file.size,
            content_type=guess_type(file.filename)[0],
            storage_path=str(file_path.relative_to(self.storage_dir)),
            uploader_id=user_id,
            upload_time=datetime.now().astimezone(tz=timezone.utc),
        )
        session.add(file_info)
        await session.commit()

        return file_info

    async def get_file_info(self, file_id: uuid.UUID, session: AsyncSession):
        result = await session.execute(select(UploadedFileInfo).where(UploadedFileInfo.id == file_id))
        file_info = result.scalars().first()
        return file_info

    def get_absolute_path(self, path: str) -> Path:
        return self.storage_dir / path
