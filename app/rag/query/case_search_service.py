# -*- coding: utf-8 -*-
"""
案例检索服务
作用：从典型案例库中检索相似故障案例
参考老师 answer_service.py 的代码风格
"""
from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState
from app.infra.vectorstore.milvus_gateway import milvus_gateway
from app.infra.llm.providers import llm_provider


@step_log("validate_case_state")
def validate_case_state(state: QueryGraphState):
    """校验案例检索所需参数"""
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        logger.error("rewritten_query 为空，无法进行案例检索")
        raise ValueError("rewritten_query 为空，无法进行案例检索")
    return rewritten_query


def search_cases(state: QueryGraphState) -> QueryGraphState:
    """
    案例检索主函数（参考老师 answer_service.py 风格）
    
    输入：state（包含 rewritten_query, extracted_entities）
    输出：state（新增 case_chunks 字段）
    """
    # 1. 校验参数
    rewritten_query = validate_case_state(state)
    
    # 2. 提取故障现象
    entities = state.get("extracted_entities", {})
    fault_symptom = entities.get("fault_symptom", rewritten_query)
    
    # 3. 生成查询向量
    try:
        embedding_result = llm_provider.embed_documents([fault_symptom])
        dense_vector = embedding_result.get("dense")[0]
        sparse_vector = embedding_result.get("sparse")[0]
    except Exception as e:
        logger.error(f"案例检索向量生成失败：{e}")
        state["case_chunks"] = []
        return state
    
    # 4. 构造 Milvus 搜索请求
    try:
        reqs = milvus_gateway.create_requests(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            limit=5,
        )
        
        # 5. 调用 Milvus 混合搜索
        milvus_result = milvus_gateway.hybrid_search(
            collection_name=milvus_gateway.COLLECTION_NAME,
            reqs=reqs,
            ranker_weights=(0.6, 0.4),
            norm_score=True,
            limit=5,
            output_fields=["chunk_id", "item_name", "title", "content", "part"],
        )
        
        # 6. 格式化结果
        case_chunks = []
        if milvus_result and len(milvus_result) > 0:
            for hit in milvus_result[0]:
                entity = hit.get("entity", {})
                case_chunks.append({
                    "chunk_id": hit.get("id") or entity.get("chunk_id", ""),
                    "item_name": entity.get("item_name", ""),
                    "title": entity.get("title", ""),
                    "content": entity.get("content", ""),
                    "part": entity.get("part", ""),
                    "score": hit.get("distance", 0.0),
                    "type": "case",
                })
        
        state["case_chunks"] = case_chunks
        logger.info(f"案例检索完成：{fault_symptom} → {len(case_chunks)} 条结果")
        
    except Exception as e:
        logger.error(f"案例检索失败：{e}")
        state["case_chunks"] = []
    
    return state
