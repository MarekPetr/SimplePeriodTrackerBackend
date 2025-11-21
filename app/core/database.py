from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.mongodb_url)
db = client[settings.database_name]


def get_database():
    return db
