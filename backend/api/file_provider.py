import os
import shutil
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.conf import Config
from api.models.db import UploadedFile

config = Config()


class FileProvider:
    def __init__(self, storage_dir: Path = None, max_size: int = None):
        self.max_size = max_size or config.data.max_upload_size
        self.storage_dir = storage_dir or (Path(config.data.data_dir) / "uploads")
        if not self.storage_dir.exists():
            self.storage_dir.mkdir()

    async def save_file(self, file: UploadFile, user_id: int, session: AsyncSession):
        file_name = f"{uuid.uuid4()}.dat"
        file_path = self.storage_dir / file_name

        async with aiofiles.open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)  # read by 1MB chunk
                if not chunk:
                    break
                await buffer.write(chunk)

        file_info = UploadedFile(
            original_filename=file.filename,
            size=file.size,
            storage_path=str(file_path.relative_to(self.storage_dir)),
            uploader_id=user_id
        )
        session.add(file_info)
        await session.commit()

        return file_info

    async def get_file_info(self, file_id: uuid.UUID, session: AsyncSession):
        result = await session.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        file_info = result.scalars().first()
        return file_info

    async def get_file_path(self, file_uuid: uuid.UUID, session: AsyncSession):
        file_info = await self.get_file_info(file_uuid, session)
        if file_info:
            return self.storage_dir / file_info.storage_path
        raise FileNotFoundError(f"file {file_uuid} not found")
