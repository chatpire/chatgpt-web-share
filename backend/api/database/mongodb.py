from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from api.conf import Config
from api.models.doc import OpenaiApiConversationHistoryDocument, OpenaiWebConversationHistoryDocument, AskLogDocument, \
    RequestLogDocument
from utils.logger import get_logger

logger = get_logger(__name__)
config = Config()

DATABASE_NAME = "cws"
client: AsyncIOMotorClient | None = None


async def init_mongodb():
    global client
    client = AsyncIOMotorClient(config.data.mongodb_url)
    await init_beanie(database=client[DATABASE_NAME],
                      document_models=[OpenaiApiConversationHistoryDocument, OpenaiWebConversationHistoryDocument, AskLogDocument,
                                       RequestLogDocument])
    # 展示当前mongodb数据库用量
    db = client[DATABASE_NAME]
    stats = await db.command({"dbStats": 1})
    logger.info(
        f"MongoDB initialized. dataSize: {stats['dataSize'] / 1024 / 1024:.2f} MB, objects: {stats['objects']}")
    await handle_timeseries()


async def handle_timeseries():
    """
    对于 AskStatDocument 和 HTTPRequestStatDocument, 当 expireAfterSeconds 更改时，beanie 并不会自动更改
    此时需要主动更改
    """
    global client
    assert client is not None, "MongoDB not initialized"
    db = client[DATABASE_NAME]
    time_series_docs = [AskLogDocument, RequestLogDocument]
    config_ttls = [config.stats.ask_stats_ttl, config.stats.request_stats_ttl]
    for doc, config_ttl in zip(time_series_docs, config_ttls):
        collection_name = doc.get_collection_name()
        coll_info = await db.command({"listCollections": 1, "filter": {"name": collection_name}})
        if not coll_info["cursor"]["firstBatch"]:
            logger.error(f"Collection {collection_name} not found")
            continue
        current_ttl = coll_info["cursor"]["firstBatch"][0]["options"]["expireAfterSeconds"]

        # 关闭自动过期
        if current_ttl != "off" and config_ttl == -1:
            await db.command({
                "collMod": collection_name,
                "expireAfterSeconds": "off"
            })
            logger.info(f"Auto expire of collection {collection_name} disabled")
            continue

        # 更改过期时间
        if current_ttl != config_ttl:
            logger.info(f"Updating TTL of collection {collection_name} from {current_ttl} to {config_ttl}")
            db.command({
                "collMod": collection_name,
                "expireAfterSeconds": config_ttl
            })
        else:
            logger.debug(f"TTL of collection {collection_name} not change: {config_ttl}")
