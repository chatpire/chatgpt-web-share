from datetime import datetime
from typing import Optional

from pydantic import BaseModel
import uuid

from api.enums.options import OpenaiWebFileUploadStrategyOption
from api.models.json import UploadedFileOpenaiWebInfo


class UploadedFileInfoSchema(BaseModel):
    id: uuid.UUID
    original_filename: str
    size: int
    storage_path: Optional[str]
    content_type: Optional[str]
    upload_time: datetime
    uploader_id: int
    openai_web_info: Optional[UploadedFileOpenaiWebInfo]

    class Config:
        orm_mode = True


class StartUploadResponseSchema(BaseModel):
    strategy: OpenaiWebFileUploadStrategyOption
    file_max_size: int
    upload_file_info: Optional[UploadedFileInfoSchema]  # 为空意味着后端不暂存文件，前端直接上传到openai
