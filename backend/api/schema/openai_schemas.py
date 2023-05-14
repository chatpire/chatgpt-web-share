from typing import Literal, Optional

from pydantic import BaseModel


class OpenAIChatResponseChoice(BaseModel):
    index: Optional[int]
    message: Optional[dict[Literal["role", "content"], str]]
    delta: Optional[dict[Literal["role", "content"], str]]
    finish_reason: Optional[str]


class OpenAIChatResponseUsage(BaseModel):
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]


class OpenAIChatResponse(BaseModel):
    choices: Optional[list[OpenAIChatResponseChoice]]
    usage: Optional[OpenAIChatResponseUsage]
