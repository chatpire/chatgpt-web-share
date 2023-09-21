from typing import Optional, Literal, Any

from pydantic import BaseModel


class OpenaiWebChatMessageMetadataAggregateResultMessage(BaseModel):
    message_type: Optional[Literal['image', 'stream'] | str]
    time: Optional[float]
    sender: Optional[Literal['server'] | str]
    # image
    image_url: Optional[str]
    # stream
    stream_name: Optional[str]
    text: Optional[str]


class OpenaiWebChatMessageMetadataAggregateResult(BaseModel):
    status: Optional[Literal['failed_with_in_kernel_exception', 'success'] | str]
    run_id: Optional[str]
    start_time: Optional[float]
    update_time: Optional[float]
    end_time: Optional[float]
    final_expression_output: Optional[Any]
    code: Optional[str]
    in_kernel_exception: Optional[dict[str, Any]]  # name, traceback [], args [], notes []
    messages: Optional[list[OpenaiWebChatMessageMetadataAggregateResultMessage]]
    jupyter_messages: Optional[list[Any]]
