from enum import auto
from strenum import StrEnum


class RevChatStatus(StrEnum):
    asking = auto()
    queueing = auto()
    idling = auto()
