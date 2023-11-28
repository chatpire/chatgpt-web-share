from typing import Optional, Literal, Any

from pydantic import BaseModel


class OpenaiWebChatMessageMetadataAttachment(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None
    size: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None
    mimeType: Optional[str] = None


class OpenaiWebChatMessageMetadataAggregateResultMessage(BaseModel):
    message_type: Optional[Literal['image', 'stream'] | str] = None
    time: Optional[float] = None
    sender: Optional[Literal['server'] | str] = None
    # image
    image_url: Optional[str] = None
    # stream
    stream_name: Optional[str] = None
    text: Optional[str] = None


class OpenaiWebChatMessageMetadataAggregateResult(BaseModel):
    status: Optional[Literal['failed_with_in_kernel_exception', 'success'] | str] = None
    run_id: Optional[str] = None
    start_time: Optional[float] = None
    update_time: Optional[float] = None
    end_time: Optional[float] = None
    final_expression_output: Optional[Any] = None
    code: Optional[str] = None
    in_kernel_exception: Optional[dict[str, Any]] = None  # name, traceback [], args [], notes []
    messages: Optional[list[OpenaiWebChatMessageMetadataAggregateResultMessage]] = None
    jupyter_messages: Optional[list[Any]] = None
