from enum import auto
from strenum import StrEnum


class OpenaiWebChatStatus(StrEnum):
    asking = auto()
    queueing = auto()
    idling = auto()
