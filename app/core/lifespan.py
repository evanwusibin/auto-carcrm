from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.shared.runtime.logger import logger
from app.shared.model.embedding_utils import get_bge_m3_ef
from app.shared.model.reranker_utils import get_reranker_model
from app.shared.clients.minio_utils import get_minio_client
from app.shared.clients.mongo_business_utils import get_business_db
from app.shared.clients.mongo_knowledge_utils import get_knowledge_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('应用启动：开始初始化基础依赖')
    try:
        get_business_db()
        get_knowledge_db()
        get_minio_client()
    except Exception:
        logger.exception('启动阶段初始化数据库或对象存储失败')

    try:
        get_bge_m3_ef()
    except Exception:
        logger.exception('启动阶段预热 Embedding 模型失败')

    try:
        get_reranker_model()
    except Exception:
        logger.exception('启动阶段预热 Reranker 模型失败')

    yield
    logger.info('应用关闭：基础资源释放完成')
