import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from pydantic import ValidationError

from api.conf import Config, Credentials
from api.enums import OpenaiApiChatModels, ChatSourceTypes
from api.exceptions import OpenaiApiException
from api.models.doc import OpenaiApiChatMessage, OpenaiApiConversationHistoryDocument, OpenaiApiChatMessageMetadata, \
    OpenaiApiChatMessageTextContent
from api.schemas.openai_schemas import OpenaiChatResponse
from utils.common import singleton_with_lock
from utils.logger import get_logger

logger = get_logger(__name__)

config = Config()
credentials = Credentials()

MAX_CONTEXT_MESSAGE_COUNT = 1000


async def _check_response(response: httpx.Response) -> None:
    # 改成自带的错误处理
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        await response.aread()
        error = OpenaiApiException(
            message=response.text,
            code=response.status_code,
        )
        raise error from ex


def make_session() -> httpx.AsyncClient:
    if config.openai_api.proxy is not None:
        proxies = {
            "http://": config.openai_api.proxy,
            "https://": config.openai_api.proxy,
        }
        session = httpx.AsyncClient(proxies=proxies, timeout=None)
    else:
        session = httpx.AsyncClient(timeout=None)
    return session


@singleton_with_lock
class OpenaiApiChatManager:
    """
    OpenAI API Manager
    """

    def __init__(self):
        self.session = make_session()

    def reset_session(self):
        self.session = make_session()

    async def complete(self, text_content: str, conversation_id: uuid.UUID = None,
                       parent_message_id: uuid.UUID = None, model: OpenaiApiChatModels = None,
                       context_message_count: int = -1, extra_args: Optional[dict] = None, **_kwargs):

        assert config.openai_api.enabled, "openai_api is not enabled"

        now_time = datetime.now().astimezone(tz=timezone.utc)
        message_id = uuid.uuid4()
        new_message = OpenaiApiChatMessage(
            source="openai_api",
            id=message_id,
            role="user",
            create_time=now_time,
            parent=parent_message_id,
            children=[],
            content=OpenaiApiChatMessageTextContent(content_type="text", text=text_content),
            metadata=OpenaiApiChatMessageMetadata(
                source="openai_api",
            )
        )

        messages = []

        if not conversation_id:
            assert parent_message_id is None, "parent_id must be None when conversation_id is None"
            messages = [new_message]
        else:
            conv_history = await OpenaiApiConversationHistoryDocument.get(conversation_id)
            if not conv_history:
                raise ValueError("conversation_id not found")
            if conv_history.source != ChatSourceTypes.openai_api:
                raise ValueError(f"{conversation_id} is not api conversation")
            if not conv_history.mapping.get(str(parent_message_id)):
                raise ValueError(f"{parent_message_id} is not a valid parent of {conversation_id}")

            # 从 current_node 开始往前找 context_message_count 个 message
            if not conv_history.current_node:
                raise ValueError(f"{conversation_id} current_node is None")

            msg = conv_history.mapping.get(str(conv_history.current_node))
            assert msg, f"{conv_history.id} current_node({conv_history.current_node}) not found in mapping"

            count = 0
            iter_count = 0

            while msg:
                count += 1
                messages.append(msg)
                if context_message_count != -1 and count >= context_message_count:
                    break
                iter_count += 1
                if iter_count > MAX_CONTEXT_MESSAGE_COUNT:
                    raise ValueError(f"too many messages to iterate, conversation_id={conversation_id}")
                msg = conv_history.mapping.get(str(msg.parent))

            messages.reverse()
            messages.append(new_message)

        # TODO: credits 判断

        base_url = config.openai_api.openai_base_url
        data = {
            "model": model.code(),
            "messages": [{"role": msg.role, "content": msg.content.text} for msg in messages],
            "stream": True,
            **(extra_args or {})
        }

        reply_message = None
        text_content = ""

        timeout = httpx.Timeout(config.openai_api.read_timeout, connect=config.openai_api.connect_timeout)

        async with self.session.stream(
                method="POST",
                url=f"{base_url}chat/completions",
                json=data,
                headers={"Authorization": f"Bearer {credentials.openai_api_key}"},
                timeout=timeout
        ) as response:
            await _check_response(response)
            async for line in response.aiter_lines():
                if not line or line is None:
                    continue
                if "data: " in line:
                    line = line[6:]
                if "[DONE]" in line:
                    break

                try:
                    line = json.loads(line)
                    resp = OpenaiChatResponse.model_validate(line)

                    if not resp.choices or len(resp.choices) == 0:
                        continue

                    if resp.choices[0].message is not None:
                        text_content = resp.choices[0].message.get("content")
                    if resp.choices[0].delta is not None:
                        text_content += resp.choices[0].delta.get("content", "")
                    if reply_message is None:
                        reply_message = OpenaiApiChatMessage(
                            source="openai_api",
                            id=uuid.uuid4(),
                            role="assistant",
                            model=model,
                            create_time=datetime.now().astimezone(tz=timezone.utc),
                            parent=message_id,
                            children=[],
                            content=OpenaiApiChatMessageTextContent(content_type="text", text=text_content),
                            metadata=OpenaiApiChatMessageMetadata(
                                source="openai_api",
                                finish_reason=resp.choices[0].finish_reason,
                            )
                        )
                    else:
                        reply_message.content = OpenaiApiChatMessageTextContent(content_type="text", text=text_content)

                    if resp.usage:
                        reply_message.metadata.usage = resp.usage

                    yield reply_message

                except json.decoder.JSONDecodeError:
                    logger.warning(f"OpenAIChatResponse parse json error")
                except ValidationError as e:
                    logger.warning(f"OpenAIChatResponse validate error: {e}")
