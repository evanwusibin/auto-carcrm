"""Mongo 知识库客户端。"""
from pymongo import MongoClient

from app.shared.config.common import env_str

_knowledge_client = None
_knowledge_db = None


def get_knowledge_db():
    global _knowledge_client, _knowledge_db
    if _knowledge_db is None:
        _knowledge_client = MongoClient(env_str('MONGO_URL'))
        _knowledge_db = _knowledge_client[env_str('MONGO_KNOWLEDGE_DB', env_str('MONGO_DB_NAME', 'auto_carcrm'))]
    return _knowledge_db
