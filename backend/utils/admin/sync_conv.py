import dateutil.parser
from dateutil.tz import tzutc
from httpx import HTTPError
from sqlalchemy import select

from api.conf import Config
from api.database.sqlalchemy import get_async_session_context
from api.exceptions import OpenaiWebException
from api.models.db import OpenaiWebConversation
from api.sources import OpenaiWebChatManager
from utils.logger import get_logger

logger = get_logger(__name__)

manager = OpenaiWebChatManager()
config = Config()


async def update_conversations(nonteam_conversations: list[dict], team_conversations: list[dict]):
    async with get_async_session_context() as session:
        r = await session.execute(select(OpenaiWebConversation))
        existed_conversations: list[OpenaiWebConversation] = r.scalars().all()

        merged_conversations = {conv["id"]: (conv, False) for conv in nonteam_conversations} | \
                               {conv["id"]: (conv, True) for conv in team_conversations}

        for conv_db in existed_conversations:
            result = merged_conversations.get(str(conv_db.conversation_id), None)
            if result:
                same_one_in_openai_server, is_team = result
                # 同步标题
                if same_one_in_openai_server["title"] != conv_db.title:
                    conv_db.title = same_one_in_openai_server["title"]
                    logger.info(
                        'Team ' if is_team else '' + f"Conversation {conv_db.conversation_id} title changed: {conv_db.title}")
                # 同步时间
                create_time = dateutil.parser.isoparse(same_one_in_openai_server["create_time"]).astimezone(tzutc())
                if create_time != conv_db.create_time:
                    conv_db.create_time = create_time
                    logger.info(
                        'Team ' if is_team else '' + f"Conversation {conv_db.conversation_id} create time changed：{conv_db.create_time}")
                # 更新 source_id
                if is_team and conv_db.source_id is None:
                    assert config.openai_web.team_account_id is not None, "team_account_id is None"
                    conv_db.source_id = config.openai_web.team_account_id
                    logger.info(f"Team Conversation {conv_db.conversation_id} source_id updated to {conv_db.source_id}")
                session.add(conv_db)
                merged_conversations.pop(str(conv_db.conversation_id))
            else:
                if conv_db.is_valid:  # 数据库中存在，但 ChatGPT 中（可能）不存在
                    conv_db.is_valid = False
                    logger.info(
                        f"Conversation [{conv_db.title}]({conv_db.conversation_id}) may be deleted, marked as invalid.")
                    session.add(conv_db)

        # 新增对话
        for same_one_in_openai_server, is_team in merged_conversations.values():
            new_conv = OpenaiWebConversation(
                conversation_id=same_one_in_openai_server["id"],
                title=same_one_in_openai_server["title"],
                is_valid=True,
                create_time=dateutil.parser.isoparse(same_one_in_openai_server["create_time"]),
                source_id=config.openai_web.team_account_id if is_team else None
            )
            session.add(new_conv)
            logger.info('Team: ' if is_team else '' +
                                                 f"Add new conversation [{new_conv.title}]({new_conv.conversation_id})")

        await session.commit()


async def sync_conversations() -> Exception | None:
    try:
        logger.info("Start syncing conversations...")
        non_team_result = await manager.get_conversations(use_team=False)
        logger.info(f"Fetched {len(non_team_result)} conversations from ChatGPT Personal account.")

        if config.openai_web.enable_team_subscription:
            if config.openai_web.team_account_id is None:
                return ValueError("Team account id is None. Please set team_account_id in config.")
            team_result = await manager.get_conversations(use_team=True)
            logger.info(f"Fetched {len(team_result)} conversations from ChatGPT Team account.")
        else:
            team_result = []

        await update_conversations(non_team_result, team_result)

        logger.info("Sync conversations finished.")
        return None
    except OpenaiWebException as e:
        logger.error(f"Fetch conversation error ({e.__class__.__name__}) {e.code}: {e.message}")
        logger.warning("Sync conversations on startup failed!")
        return e
    # except HTTPError as e:
    #     logger.error(f"Fetch conversation error ({e.__class__.__name__}) {str(e)}")
    #     logger.warning("Sync conversations on startup failed!")
    #     return e
    except Exception as e:
        logger.error(f"Fetch conversation error ({e.__class__.__name__}) {str(e)}")
        logger.warning("Sync conversations on startup failed!")
        return e
