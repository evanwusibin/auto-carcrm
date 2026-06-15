# -*- coding: utf-8 -*-
"""
知识文档持久化服务
作用：将导入的文档元信息保存到MongoDB，支持文档管理和查询
"""
from datetime import datetime
from app.shared.runtime.logger import logger, step_log
from app.process.import_.agent.state import ImportGraphState
from app.infra.persistence.knowledge_repository import knowledge_repository


@step_log("persist_knowledge")
# 持久化记忆
def persist_knowledge(state: ImportGraphState) -> ImportGraphState:
    """
    将知识文档的元信息持久化到MongoDB
    1. 从state获取文档信息
    2. 构造文档对象
    3. 保存到MongoDB
    4. 回写knowledge_doc_id到state
    """
    # 1. 获取参数
    file_title = state.get("file_title", "")
    item_name = state.get("item_name", "")
    chunks = state.get("chunks", [])
    md_content = state.get("md_content", "")
    
    # 从state顶层字段读取元数据（由doc_meta_service写入）
    vehicle_model = state.get("vehicle_model", "")
    version = state.get("version", "") or state.get("doc_version", "")
    doc_type = state.get("doc_type", "")
    effective_date = state.get("effective_date", "")
    expire_date = state.get("expire_date", "")
    
    # 2. 构造文档对象
    knowledge_document = {
        "title": file_title,
        "item_name": item_name,
        "vehicle_model": vehicle_model,
        "version": version,
        "doc_type": doc_type,
        "effective_date": effective_date,
        "expire_date": expire_date,
        "source_type": "manual",
        "tags": [],
        "chunk_count": len(chunks),
        "content_length": len(md_content),
        "status": "draft",  # 初始状态：草稿
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    # 3. 保存到MongoDB
    try:
        inserted_id = knowledge_repository.save(knowledge_document)
        logger.info(f"知识文档保存成功: {file_title}, id={inserted_id}")
        state["knowledge_doc_id"] = str(inserted_id)
    except Exception as e:
        logger.error(f"知识文档保存失败: {e}")
        raise
    
    return state


@step_log("publish_knowledge")
def publish_knowledge(state: ImportGraphState) -> ImportGraphState:
    """
    将知识文档状态从draft改为published
    1. 获取knowledge_doc_id
    2. 判断是否自动发布
    3. 更新状态为published
    """
    # 1. 获取参数
    knowledge_doc_id = state.get("knowledge_doc_id")
    is_auto_publish = state.get("is_auto_publish", True)
    
    if not knowledge_doc_id:
        logger.warning("knowledge_doc_id为空，跳过发布")
        state["import_status"] = "completed"
        return state
    
    # 2. 更新状态
    if is_auto_publish:
        try:
            knowledge_repository.update_status(knowledge_doc_id, "published")
            logger.info(f"知识文档发布成功: {knowledge_doc_id}")
        except Exception as e:
            logger.error(f"知识文档发布失败: {e}")
            raise
    else:
        logger.info(f"知识文档保持draft状态，等待人工审核: {knowledge_doc_id}")
    
    # 3. 写入状态
    state["import_status"] = "completed"
    return state
