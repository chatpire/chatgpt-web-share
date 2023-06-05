from enum import auto
from strenum import StrEnum


class WebChatStatus(StrEnum):
    asking = auto()
    queueing = auto()
    idling = auto()
