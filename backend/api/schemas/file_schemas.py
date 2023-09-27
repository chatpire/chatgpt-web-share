from datetime import datetime
from typing import Optional

from pydantic import BaseModel
import uuid

from api.models.json import OpenaiWebChatFileInfo


class UploadedFileInfoSchema(BaseModel):
    id: uuid.UUID
    original_filename: str
    size: int
    storage_path: str
    content_type: Optional[str]
    upload_time: datetime
    uploader_id: int
    openai_web_info: Optional[OpenaiWebChatFileInfo]

    class Config:
        orm_mode = True
