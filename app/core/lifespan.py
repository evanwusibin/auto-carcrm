# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.shared.runtime.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("应用启动：开始初始化基础依赖")
    try:
        from app.shared.clients.mongo_business_utils import get_business_db
        get_business_db()
        logger.info("MongoDB 业务库连接成功")
    except Exception:
        logger.exception("MongoDB 业务库连接失败")

    try:
        from app.shared.clients.mongo_knowledge_utils import get_knowledge_db
        get_knowledge_db()
        logger.info("MongoDB 知识库连接成功")
    except Exception:
        logger.exception("MongoDB 知识库连接失败")

    try:
        from app.shared.clients.minio_utils import get_minio_client
        get_minio_client()
        logger.info("MinIO 客户端初始化成功")
    except Exception:
        logger.exception("MinIO 客户端初始化失败")

    try:
        from app.shared.model.embedding_utils import get_bge_m3_ef
        get_bge_m3_ef()
        logger.info("Embedding 模型预热完成")
    except Exception:
        logger.exception("Embedding 模型预热失败")

    try:
        from app.shared.model.reranker_utils import get_reranker_model
        get_reranker_model()
        logger.info("Reranker 模型预热完成")
    except Exception:
        logger.exception("Reranker 模型预热失败")

    logger.info("应用启动完成，所有基础依赖已初始化")
    yield
    logger.info("应用关闭：基础资源释放完成")
