from enum import auto
from strenum import StrEnum


class OpenaiWebFileUploadStrategyOption(StrEnum):
    disable_upload = auto()
    server_upload_only = auto()
    browser_upload_only = auto()
    browser_upload_when_file_size_exceed = auto()
