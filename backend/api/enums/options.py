from enum import auto
from strenum import StrEnum


class OpenaiWebFileUploadStrategyOption(StrEnum):
    server_upload_only = auto()
    browser_upload_only = auto()
    browser_upload_when_file_size_exceed = auto()
