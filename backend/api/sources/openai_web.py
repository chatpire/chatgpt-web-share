import asyncio
import json
import uuid
from mimetypes import guess_type

import websockets
import base64

import aiofiles
import httpx
from fastapi.encoders import jsonable_encoder
import aiohttp
from httpx import AsyncClient
from pydantic import ValidationError

from api.conf import Config, Credentials
from api.enums import OpenaiWebChatModels
from api.exceptions import InvalidParamsException, OpenaiWebException, ResourceNotFoundException
from api.file_provider import FileProvider
from api.models.doc import OpenaiWebChatMessageMetadata, OpenaiWebConversationHistoryDocument, \
    OpenaiWebConversationHistoryMeta, OpenaiWebChatMessage, OpenaiWebChatMessageTextContent, \
    OpenaiWebChatMessageCodeContent, \
    OpenaiWebChatMessageTetherBrowsingDisplayContent, OpenaiWebChatMessageTetherQuoteContent, \
    OpenaiWebChatMessageSystemErrorContent, OpenaiWebChatMessageStderrContent, \
    OpenaiWebChatMessageExecutionOutputContent, OpenaiWebChatMessageMultimodalTextContent, \
    OpenaiWebChatMessageMultimodalTextContentImagePart, OpenaiWebChatMessageMetadataAttachment
from api.models.json import UploadedFileOpenaiWebInfo
from api.schemas.file_schemas import UploadedFileInfoSchema
from api.schemas.openai_schemas import OpenaiChatPlugin, OpenaiChatPluginUserSettings, OpenaiChatFileUploadUrlRequest, \
    OpenaiChatFileUploadUrlResponse, OpenaiWebCompleteRequest, \
    OpenaiWebCompleteRequestConversationMode, OpenaiChatPluginListResponse, OpenaiWebAccountsCheckResponse
from utils.common import SingletonMeta
from utils.logger import get_logger

config = Config()
credentials = Credentials()
logger = get_logger(__name__)


def convert_openai_web_message(item: dict, message_id: str = None) -> OpenaiWebChatMessage | None:
    if not item.get("message"):
        return None
    if not item["message"].get("author"):
        logger.debug(f"Parse message {message_id}: Unknown author")

    content = None
    fallback_content = None
    if item["message"].get("content"):
        content_type = item["message"]["content"].get("content_type")
        content_map = {
            "text": OpenaiWebChatMessageTextContent,
            "multimodal_text": OpenaiWebChatMessageMultimodalTextContent,
            "code": OpenaiWebChatMessageCodeContent,
            "execution_output": OpenaiWebChatMessageExecutionOutputContent,
            "stderr": OpenaiWebChatMessageStderrContent,
            "tether_browsing_display": OpenaiWebChatMessageTetherBrowsingDisplayContent,
            "tether_quote": OpenaiWebChatMessageTetherQuoteContent,
            "system_error": OpenaiWebChatMessageSystemErrorContent
        }
        if content_type not in content_map:
            logger.debug(f"Parse message: Unknown content type {content_type}")
            fallback_content = item["message"]["content"]
        else:
            content = content_map[content_type](**item["message"]["content"])

    message_id = message_id or item["message"]["id"]
    result = OpenaiWebChatMessage(
        source="openai_web",
        id=message_id,  # 这里观察到message_id和mapping中的id不一样，暂时先使用mapping中的id
        role=item["message"]["author"]["role"],
        author_name=item["message"]["author"].get("name"),
        model=None,
        create_time=item["message"].get("create_time"),
        parent=item.get("parent"),
        children=item.get("children", []),
        content=content
    )
    metadata_dict = OpenaiWebChatMessageMetadata(
        source="openai_web",
        weight=item["message"].get("weight"),
        end_turn=item["message"].get("end_turn"),
        recipient=item["message"].get("recipient"),
        message_status=item["message"].get("status"),
        fallback_content=fallback_content,
    ).model_dump(exclude_unset=True, exclude_none=True)
    if "metadata" in item["message"] and item["message"]["metadata"] != {}:
        metadata_dict.update(item["message"]["metadata"])
        metadata = OpenaiWebChatMessageMetadata.model_validate(metadata_dict)
        result.metadata = metadata
        model_code = item["message"]["metadata"].get("model_slug")
        result.model = OpenaiWebChatModels.from_code(model_code) or model_code
    else:
        result.metadata = OpenaiWebChatMessageMetadata.model_validate(metadata_dict)
    return result


def convert_mapping(mapping: dict[uuid.UUID, dict]) -> dict[str, OpenaiWebChatMessage]:
    result = {}
    if not mapping:
        return result
    for key, item in mapping.items():
        message = convert_openai_web_message(item, str(key))
        if message:
            result[key] = message
    return {str(key): value for key, value in result.items()}


def get_latest_model_from_mapping(current_node_uuid: str | None,
                                  mapping: dict[str, OpenaiWebChatMessage]) -> OpenaiWebChatModels | None:
    model = None
    if not current_node_uuid:
        return model
    try:
        msg: OpenaiWebChatMessage = mapping.get(current_node_uuid)
        while msg:
            if msg.model:
                model = msg.model
                break
            msg = mapping.get(str(msg.parent))
    finally:
        return model


def _check_fields(data: dict) -> bool:
    try:
        data["message"]["content"]
    except (TypeError, KeyError):
        return False
    return True


async def _check_response(response: httpx.Response) -> None:
    # 改成自带的错误处理
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        await response.aread()
        error = OpenaiWebException(
            message=response.text,
            code=response.status_code,
        )
        raise error from ex


def default_header():
    return {
        # "Accept": "text/event-stream",
        "Authorization": f"Bearer {credentials.openai_web_access_token}",
        "Content-Type": "application/json",
        # "X-Openai-Assistant-App-Id": "",
        # "Connection": "close",
        "Accept-Language": "en-US",
        "Referer": "https://chat.openai.com/",
    }


def req_headers(use_team: bool = False):
    if not use_team:
        return {}
    else:
        if not config.openai_web.team_account_id:
            raise InvalidParamsException(
                "ChatGPT account id is not set in setting. Please set it before using team subscription.")
        return {
            "Chatgpt-Account-Id": config.openai_web.team_account_id
        }


def team_headers(chatgpt_account_id: str = None):
    if not chatgpt_account_id:
        return {}
    return {
        "Chatgpt-Account-Id": chatgpt_account_id
    }


def make_session() -> httpx.AsyncClient:
    if config.openai_web.proxy is not None and config.openai_web.proxy != "":
        proxies = {
            "http://": config.openai_web.proxy,
            "https://": config.openai_web.proxy,
        }
        session = httpx.AsyncClient(proxies=proxies, timeout=config.openai_web.common_timeout)
    else:
        session = httpx.AsyncClient(timeout=config.openai_web.common_timeout)
    session.headers.clear()
    session.headers.update(default_header())
    return session


async def _receive_from_websocket(wss_url):
    timeout = Config().openai_web.common_timeout
    wss_proxy = Config().openai_web.wss_proxy
    recv_msg_count = 0
    timeout_settings = aiohttp.ClientTimeout(total=None, connect=timeout, sock_read=timeout)

    async with aiohttp.ClientSession(timeout=timeout_settings) as session:
        async with session.ws_connect(wss_url, protocols=["json.reliable.webpubsub.azure.v1"], proxy=wss_proxy) as ws:
            logger.debug(f"Connected to Websocket {wss_url[:65]}...{wss_url[-10:]}")
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    message = json.loads(msg.data)
                    if "data" not in message:
                        continue
                    sequence_id = message["sequenceId"]
                    data = base64.b64decode(message['data']['body']).decode('utf-8')
                    if not data or data is None:
                        continue
                    if "data: " in data:
                        data = data[6:]
                    if "[DONE]" in data:
                        # send ack to server
                        await ws.send_json({"type": "sequenceAck", "sequenceId": sequence_id})
                        break
                    try:
                        data = json.loads(data)
                    except json.decoder.JSONDecodeError:
                        continue
                    if not _check_fields(data):
                        if "error" in data:
                            raise OpenaiWebException(data["error"])
                        else:
                            logger.warning(f"Field missing. Details: {str(data)}")
                            continue
                    recv_msg_count += 1
                    # batch ack to server every 10 messages
                    if recv_msg_count > 10:
                        await ws.send_json({"type": "sequenceAck", "sequenceId": sequence_id})
                        recv_msg_count = 0
                    yield data
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error("WebSocket connection closed with exception %s" % ws.exception())
                    break
    logger.debug("Connection closed.")


class OpenaiWebChatManager(metaclass=SingletonMeta):
    def __init__(self):
        self.semaphore = asyncio.Semaphore(config.openai_web.max_completion_concurrency)
        self.session: AsyncClient | None = None
        self.reset_session()

    def is_busy(self):
        return self.semaphore.locked()

    def reset_session(self):
        self.session = make_session()

    async def check_accounts(self) -> OpenaiWebAccountsCheckResponse:
        url = f"{config.openai_web.chatgpt_base_url}accounts/check/v4-2023-04-27"
        response = await self.session.get(url)
        result = json.loads(response.text)
        result = OpenaiWebAccountsCheckResponse(**result)
        return result

    async def get_conversations(self, timeout=None, use_team: bool = False) -> list[dict]:
        if timeout is None:
            timeout = httpx.Timeout(config.openai_web.common_timeout)

        offset = 0
        limit = 80
        _results = []
        while True:
            url = f"{config.openai_web.chatgpt_base_url}conversations?offset={offset}&limit={limit}"
            response = await self.session.get(url, timeout=timeout, headers=req_headers(use_team))
            await _check_response(response)
            data = json.loads(response.text)
            conversations = data["items"]
            if len(conversations):
                _results.extend(conversations)
            else:
                break
            offset += 80

        return _results

    async def get_conversation_history(self, conversation_id: uuid.UUID | str,
                                       source_id: str = None) -> OpenaiWebConversationHistoryDocument:
        url = f"{config.openai_web.chatgpt_base_url}conversation/{conversation_id}"
        response = await self.session.get(url, timeout=None, headers=team_headers(source_id))
        response.encoding = 'utf-8'
        await _check_response(response)
        result = json.loads(response.text)
        try:
            mapping = convert_mapping(result.get("mapping"))
        except Exception as e:
            raise InvalidParamsException(f"Failed to convert mapping: {e}")
        current_model = None
        if mapping.get(result.get("current_node")):
            current_model = get_latest_model_from_mapping(result["current_node"], mapping)
        doc = OpenaiWebConversationHistoryDocument(
            source="openai_web",
            _id=conversation_id,
            title=result.get("title"),
            create_time=result.get("create_time"),
            update_time=result.get("update_time"),
            mapping=mapping,
            current_node=result.get("current_node"),
            current_model=current_model,
            metadata=OpenaiWebConversationHistoryMeta(
                source="openai_web",
                plugin_ids=result.get("plugin_ids"),
                moderation_results=result.get("moderation_results"),
                gizmo_id=result.get("gizmo_id"),
                is_archived=result.get("is_archived"),
                conversation_template_id=result.get("conversation_template_id"),
            )
        )
        await doc.save()
        return doc

    async def clear_conversations(self, use_team: bool = False):
        url = f"{config.openai_web.chatgpt_base_url}conversations"
        response = await self.session.patch(url, json={"is_visible": False}, headers=req_headers(use_team))
        await _check_response(response)

    async def complete(self, model: OpenaiWebChatModels, text_content: str, use_team: bool,
                       conversation_id: uuid.UUID = None,
                       parent_message_id: uuid.UUID = None,
                       plugin_ids: list[str] = None,
                       attachments: list[OpenaiWebChatMessageMetadataAttachment] = None,
                       multimodal_image_parts: list[OpenaiWebChatMessageMultimodalTextContentImagePart] = None,
                       **_kwargs):

        assert config.openai_web.enabled, "OpenAI Web is not enabled"

        model = model or OpenaiWebChatModels.gpt_3_5

        if plugin_ids is not None and len(plugin_ids) > 0 and model != OpenaiWebChatModels.gpt_4_plugins:
            raise InvalidParamsException("plugin_ids can only be set when model is gpt-4-plugins")

        if plugin_ids is not None and len(plugin_ids) > 0 and parent_message_id:
            raise InvalidParamsException("plugin_ids can only be set at new conversation")

        if conversation_id or parent_message_id:
            assert parent_message_id and conversation_id, "parent_message_id must be set with conversation_id"
        else:
            parent_message_id = str(uuid.uuid4())

        if text_content == ":continue":
            messages = None
            action = "continue"
        else:
            action = "next"
            if not multimodal_image_parts:
                content = OpenaiWebChatMessageTextContent(
                    content_type="text", parts=[text_content]
                )
            else:
                content = OpenaiWebChatMessageMultimodalTextContent(
                    content_type="multimodal_text", parts=multimodal_image_parts + [text_content]
                )

            messages = [
                {
                    "id": str(uuid.uuid4()),
                    "author": {"role": "user"},
                    "content": content.model_dump(),
                    "metadata": {}
                }
            ]

            if attachments and len(attachments) > 0:
                messages[0]["metadata"]["attachments"] = [attachment.model_dump() for attachment in attachments]

        timeout = httpx.Timeout(Config().openai_web.common_timeout, read=Config().openai_web.ask_timeout)

        completion_request = OpenaiWebCompleteRequest(
            action=action,
            arkose_token=None,
            conversation_mode=OpenaiWebCompleteRequestConversationMode(kind="primary_assistant"),
            conversation_id=str(conversation_id) if conversation_id else None,
            messages=messages,
            parent_message_id=str(parent_message_id) if parent_message_id else None,
            model=model.code(),
            plugin_ids=plugin_ids
        ).dict(exclude_none=True)
        completion_request["arkose_token"] = None
        data_json = json.dumps(jsonable_encoder(completion_request))

        async with self.session.stream(method="POST", url=f"{config.openai_web.chatgpt_base_url}conversation",
                                       data=data_json, timeout=timeout,
                                       headers=req_headers(use_team) | {
                                           "referer": "https://chat.openai.com/" + (
                                                   f"c/{conversation_id}" if conversation_id else "")
                                       }) as response:
            await _check_response(response)

            async for line in response.aiter_lines():
                if not line or line is None:
                    continue

                # wss
                try:
                    line = json.loads(line)
                    wss_url = line.get("wss_url")
                    # connect to wss_url and receive messages
                    if wss_url:
                        async for l in _receive_from_websocket(wss_url):
                            yield l
                        break
                except json.decoder.JSONDecodeError:
                    pass

                # old way
                if "data: " in line:
                    line = line[6:]
                if "[DONE]" in line:
                    break
                try:
                    data = json.loads(line)
                    if not _check_fields(data):
                        if "error" in data:
                            logger.warning(f"error in message stream: {line}")
                            raise OpenaiWebException(data["error"])
                        else:
                            logger.warning(f"Field missing. Details: {line}")
                            continue
                    yield data
                except json.decoder.JSONDecodeError:
                    continue

    async def delete_conversation(self, conversation_id: str, source_id: str = None):
        # await self.chatbot.delete_conversation(conversation_id)
        url = f"{config.openai_web.chatgpt_base_url}conversation/{conversation_id}"
        response = await self.session.patch(url, json={"is_visible": False},
                                            headers=team_headers(source_id))
        await _check_response(response)

    async def set_conversation_title(self, conversation_id: str, title: str, source_id: str = None):
        url = f"{config.openai_web.chatgpt_base_url}conversation/{conversation_id}"
        response = await self.session.patch(url, json={"title": title},
                                            headers=team_headers(source_id))
        await _check_response(response)

    async def generate_conversation_title(self, conversation_id: str, message_id: str, use_team: bool):
        url = f"{config.openai_web.chatgpt_base_url}conversation/gen_title/{conversation_id}"
        response = await self.session.post(
            url,
            json={"message_id": message_id},
            headers=req_headers(use_team)
        )
        await _check_response(response)
        result = response.json()
        if result.get("title"):
            return result.get("title")
        else:
            raise OpenaiWebException(f"Failed to generate title: {result.get('message')}")

    async def get_installed_plugin_manifests(self, offset=0, limit=250,
                                             use_team: bool = False) -> OpenaiChatPluginListResponse:
        params = {
            "offset": offset,
            "limit": limit,
            "is_installed": True,
        }
        response = await self.session.get(
            url=f"{config.openai_web.chatgpt_base_url}aip/p",
            params=params,
            timeout=config.openai_web.common_timeout,
            headers=req_headers(use_team)
        )
        await _check_response(response)
        return OpenaiChatPluginListResponse.model_validate(response.json())

    async def get_plugin_manifests(self, offset=0, limit=8, category="", search="",
                                   use_team: bool = False) -> OpenaiChatPluginListResponse:
        if not config.openai_web.is_plus_account:
            raise InvalidParamsException("errors.notPlusChatgptAccount")
        params = {
            "offset": offset,
            "limit": limit,
            "category": category,
            "search": search,
        }
        response = await self.session.get(
            url=f"{config.openai_web.chatgpt_base_url}aip/p/approved",
            params=params,
            timeout=config.openai_web.common_timeout,
            headers=req_headers(use_team)
        )
        await _check_response(response)
        return OpenaiChatPluginListResponse.model_validate(response.json())

    # async def get_plugin_manifest(self, plugin_id: str) -> OpenaiChatPluginListResponse:
    #     response = await self.session.get(
    #         url=f"{config.openai_web.chatgpt_base_url}public/plugins/by-id",
    #         params={"ids": plugin_id},
    #     )
    #     await _check_response(response)
    #     return OpenaiChatPluginListResponse.parse_obj(response.json())

    async def change_plugin_user_settings(self, plugin_id: str, setting: OpenaiChatPluginUserSettings,
                                          use_team: bool):
        if not config.openai_web.is_plus_account:
            raise InvalidParamsException("errors.notPlusChatgptAccount")
        response = await self.session.patch(
            url=f"{config.openai_web.chatgpt_base_url}aip/p/{plugin_id}/user-settings",
            json=setting.dict(exclude_unset=True, exclude_none=True),
            headers=req_headers(use_team)
        )
        await _check_response(response)
        try:
            result = OpenaiChatPlugin.model_validate(response.json())
            return result
        except ValidationError as e:
            logger.warning(f"Failed to parse plugin: {e}")
            raise e

    async def get_interpreter_info(self, conversation_id: str, source_id: str | None):
        response = await self.session.get(
            url=f"{config.openai_web.chatgpt_base_url}conversation/{conversation_id}/interpreter",
            headers=team_headers(source_id)
        )
        await _check_response(response)
        return response.json()

    async def get_file_download_url(self, file_id: str, use_team: bool):
        response = await self.session.get(
            url=f"{config.openai_web.chatgpt_base_url}files/{file_id}/download",
            headers=req_headers(use_team)
        )
        await _check_response(response)
        result = response.json()
        if result.get("status") == "success":
            return result.get("download_url")
        else:
            raise ResourceNotFoundException(
                f"{file_id} Failed to get download url: {result.get('error_code')}({result.get('error_message')})")

    async def get_interpreter_file_download_url(self, conversation_id: str, message_id: str, sandbox_path: str,
                                                source_id: str | None):
        response = await self.session.get(
            url=f"{config.openai_web.chatgpt_base_url}conversation/{conversation_id}/interpreter/download",
            params={"message_id": message_id, "sandbox_path": sandbox_path},
            headers=team_headers(source_id)
        )
        await _check_response(response)
        result = response.json()
        if result.get("status") == "success":
            return result.get("download_url")
        else:
            raise ResourceNotFoundException(
                f"{conversation_id} Failed to get download url: {result.get('error_code')}({result.get('error_message')})")

    async def get_file_upload_url(self, upload_info: OpenaiChatFileUploadUrlRequest,
                                  use_team: bool) -> OpenaiChatFileUploadUrlResponse:
        """
        获取文件在 azure blob 的上传地址
        """
        response = await self.session.post(
            url=f"{config.openai_web.chatgpt_base_url}files",
            json=upload_info.model_dump(),
            headers=req_headers(use_team)
        )
        await _check_response(response)
        result = OpenaiChatFileUploadUrlResponse.model_validate(response.json())
        if result.status != "success":
            raise OpenaiWebException(
                f"{upload_info.file_name} Failed to get upload url from OpenAI: {result.error_code}({result.error_message})")
        return result

    async def check_file_uploaded(self, file_id: str, use_team: bool) -> str:
        """
        检查文件是否上传成功，顺便获得文件下载地址
        注意：这只能调用一次，文件未上传，或者已经调用过该接口，Openai都会返回错误
        :return: 文件下载地址
        """
        if file_id is None:
            raise InvalidParamsException()

        response = await self.session.post(
            url=f"{config.openai_web.chatgpt_base_url}files/{file_id}/uploaded",
            json={},
            headers=req_headers(use_team)
        )
        await _check_response(response)
        result = response.json()
        if result.get("status") == "success":
            return result.get("download_url")
        else:
            raise OpenaiWebException(
                f"Failed to check {file_id} uploaded: {result.get('error_code')}({result.get('error_message')}). File may be not uploaded yet.")

    async def upload_file_in_server(self, file_info: UploadedFileInfoSchema,
                                    use_team: bool) -> UploadedFileOpenaiWebInfo:
        """
        将已上传到服务器上的文件上传到OpenAI Web

        TODO 暂时无法使用，因为会被 Cloudflare 阻止
        """

        # 检查文件是否仍然存在
        file_provider = FileProvider()
        file_path = file_provider.get_absolute_path(file_info.storage_path)
        if not file_path.exists():
            raise ResourceNotFoundException(
                f"File {file_info.original_filename} ({file_info.id}) not exists. This may be caused by file cleanup.")

        # 获取 cdn 上传地址
        upload_info = OpenaiChatFileUploadUrlRequest(
            file_name=file_info.original_filename,
            file_size=file_info.size,
            use_case="my_files"
        )
        upload_response = await self.get_file_upload_url(upload_info, use_team)
        upload_url = upload_response.upload_url  # 预签名的 azure 地址

        # 上传文件
        content_type = file_info.content_type or guess_type(file_info.original_filename)[
            0] or "application/octet-stream"
        headers = self.session.headers.copy()
        headers.update({
            'x-ms-blob-type': 'BlockBlob',
            'Content-Type': content_type,
            'x-ms-version': '2020-04-08',
            'Origin': 'https://chat.openai.com',
        })
        async with aiofiles.open(file_path, mode='rb') as file:
            content = await file.read()
        async with aiohttp.ClientSession() as session:
            response = await session.put(upload_url, data=content, headers=headers)
            if response.status != 201:
                logger.error(
                    f"Failed to upload {file_info.id}: {response.status}({response.reason}): {await response.text()}")
                raise OpenaiWebException(
                    f"Failed to upload {file_info.id}: {response.status}({response.reason})")

        # 检查文件是否上传成功
        download_url = await self.check_file_uploaded(upload_response.file_id, use_team)
        openai_web_info = UploadedFileOpenaiWebInfo(
            file_id=upload_response.file_id,
            download_url=download_url,
        )

        return openai_web_info
