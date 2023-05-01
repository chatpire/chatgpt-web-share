import datetime
import uuid
from typing import Optional

from pydantic import BaseModel

from api.enums import RevChatModels


class RevConversationSchema(BaseModel):
    id: int = -1
    conversation_id: uuid.UUID | None
    title: str | None
    user_id: int | None
    is_valid: bool = True
    model_name: RevChatModels | None
    create_time: datetime.datetime | None
    active_time: datetime.datetime | None

    class Config:
        use_enum_values = True
        orm_mode = True
