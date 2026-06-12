"""Mongo 业务库客户端。"""
from pymongo import MongoClient

from app.shared.config.common import env_str

_business_client = None
_business_db = None


def get_business_db():
    global _business_client, _business_db
    if _business_db is None:
        _business_client = MongoClient(env_str('MONGO_URL'))
        _business_db = _business_client[env_str('MONGO_DB_NAME', 'auto_carcrm')]
    return _business_db
