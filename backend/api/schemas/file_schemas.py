from datetime import datetime
from typing import Optional

from pydantic import BaseModel
import uuid


class UploadedFileSchema(BaseModel):
    uuid: uuid.UUID
    original_filename: str
    size: int
    content_type: Optional[str]
    upload_date: datetime
    uploader_id: int
