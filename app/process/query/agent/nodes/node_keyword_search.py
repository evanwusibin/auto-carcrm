# -*- coding: utf-8 -*-
"""
节点：关键词检索 (node_keyword_search)
作用：使用 BM25 算法进行关键词精确检索
"""
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.keyword_search_service import search_by_keywords


@node_log("node_keyword_search")
def node_keyword_search(state: QueryGraphState) -> QueryGraphState:
    """
    节点：关键词检索
    
    作用：
    1. 使用 BM25 算法进行关键词精确检索
    2. 适用于专业术语、故障码、车型等精确匹配
    
    输入：rewritten_query, item_names, extracted_entities
    输出：keyword_chunks（关键词检索结果）
    """
    add_running_task(state.get("session_id", ""), "node_keyword_search", state.get("is_stream", False))
    
    try:
        state = search_by_keywords(state)
        logger.info(f"关键词检索完成，结果数量：{len(state.get('keyword_chunks', []))}")
    except Exception as e:
        logger.error(f"关键词检索失败：{e}")
        state["keyword_chunks"] = []
    
    add_done_task(state.get("session_id", ""), "node_keyword_search", state.get("is_stream", False))
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "rewritten_query": "P0A0F故障码是什么意思？",
        "item_names": ["HAK 180 烫金机"],
        "extracted_entities": {
            "fault_codes": "P0A0F",
        },
        "is_stream": False,
    }
    
    result = node_keyword_search(mock_state)
    print(f"关键词检索结果：{len(result.get('keyword_chunks', []))} 条")
