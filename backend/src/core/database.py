from pymongo import AsyncMongoClient
from beanie import init_beanie
from core.config import settings
from modules.models import ElectionSchema

async def init_db():
    client = AsyncMongoClient(settings.mongodb_uri)
    
    db = client.get_database("database")
    
    await init_beanie(
        database=db,
        document_models=[
            ElectionSchema,
        ]
    )