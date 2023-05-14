from typing import Literal

from pydantic import BaseModel


class OpenAIChatResponseChoice(BaseModel):
    index: int
    message: dict[Literal["role", "content"], str]
    finish_reason: str


class OpenAIChatResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int


class OpenAIChatResponse(BaseModel):
    choices: list[OpenAIChatResponseChoice]
    usage: OpenAIChatResponseUsage
