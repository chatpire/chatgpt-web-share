from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from api.conf import Config
from api.models import ConversationHistoryDocument
from utils.logger import get_logger
from motor.core import AgnosticClient

logger = get_logger(__name__)


async def init_mongodb():
    # Create Motor client
    client = AsyncIOMotorClient(
        Config().data.mongodb_url
    )

    await init_beanie(database=client.cws, document_models=[ConversationHistoryDocument])
    logger.info("MongoDB initialized")
