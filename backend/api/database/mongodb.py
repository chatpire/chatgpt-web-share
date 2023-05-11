from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from api.models import ConversationHistory


async def init_mongodb():
    # Create Motor client
    client = AsyncIOMotorClient(
        "mongodb://user:pass@host:27017"
    )

    # Initialize beanie with the Product document class and a database
    await init_beanie(database=client.db_name, document_models=[ConversationHistory])
