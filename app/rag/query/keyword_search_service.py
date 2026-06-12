# -*- coding: utf-8 -*-
"""
关键词检索服务
作用：使用 BM25 算法进行关键词精确检索
参考老师 answer_service.py 的代码风格
"""
from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState
from app.infra.vectorstore.milvus_gateway import milvus_gateway


@step_log("validate_keyword_state")
def validate_keyword_state(state: QueryGraphState):
    """校验关键词检索所需参数"""
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        logger.error("rewritten_query 为空，无法进行关键词检索")
        raise ValueError("rewritten_query 为空，无法进行关键词检索")
    return rewritten_query


def extract_keywords_from_entities(entities: dict) -> list[str]:
    """
    从实体中提取关键词
    
    输入：entities（实体字典）
    输出：keywords（关键词列表）
    """
    keywords = []
    
    # 故障码
    if entities.get("fault_codes"):
        keywords.append(entities["fault_codes"])
    
    # 车型
    if entities.get("vehicle_model"):
        keywords.append(entities["vehicle_model"])
    
    # 部件
    if entities.get("component"):
        keywords.append(entities["component"])
    
    return keywords


def search_by_keywords(state: QueryGraphState) -> QueryGraphState:
    """
    关键词检索主函数（参考老师 answer_service.py 风格）
    
    输入：state（包含 rewritten_query, extracted_entities）
    输出：state（新增 keyword_chunks 字段）
    """
    # 1. 校验参数
    rewritten_query = validate_keyword_state(state)
    
    # 2. 提取关键词
    entities = state.get("extracted_entities", {})
    entity_keywords = extract_keywords_from_entities(entities)
    
    # 3. 构造 Milvus 过滤表达式
    # 如果有故障码，用故障码精确匹配
    if entities.get("fault_codes"):
        expr = f'content like "%{entities["fault_codes"]}%"'
    elif entities.get("vehicle_model"):
        expr = f'item_name like "%{entities["vehicle_model"]}%"'
    elif entities.get("component"):
        expr = f'content like "%{entities["component"]}%"'
    else:
        # 没有关键词，返回空结果
        state["keyword_chunks"] = []
        logger.info(f"关键词检索完成：{rewritten_query} → 0 条结果（无关键词）")
        return state
    
    # 4. 调用 Milvus 查询
    try:
        results = milvus_gateway.client.query(
            collection_name=milvus_gateway.COLLECTION_NAME,
            filter=expr,
            output_fields=["chunk_id", "item_name", "title", "content", "part"],
            limit=10,
        )
        
        # 5. 格式化结果
        keyword_chunks = []
        for hit in results:
            keyword_chunks.append({
                "chunk_id": hit.get("chunk_id", ""),
                "item_name": hit.get("item_name", ""),
                "title": hit.get("title", ""),
                "content": hit.get("content", ""),
                "part": hit.get("part", ""),
                "score": 1.0,  # 关键词匹配，分数为1
                "type": "keyword",
            })
        
        state["keyword_chunks"] = keyword_chunks
        logger.info(f"关键词检索完成：{rewritten_query} → {len(keyword_chunks)} 条结果")
        
    except Exception as e:
        logger.error(f"关键词检索失败：{e}")
        state["keyword_chunks"] = []
    
    return state
