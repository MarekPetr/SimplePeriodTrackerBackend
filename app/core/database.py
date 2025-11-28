from pymongo import AsyncMongoClient
from app.core.config import settings

client = AsyncMongoClient(settings.mongodb_url)
db = client[settings.database_name]


def get_database():
    return db
