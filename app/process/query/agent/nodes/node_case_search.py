# -*- coding: utf-8 -*-
"""
节点：案例检索 (node_case_search)
作用：检索典型案例库，查找相似故障案例
"""
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.case_search_service import search_cases


@node_log("node_case_search")
def node_case_search(state: QueryGraphState) -> QueryGraphState:
    """
    节点：案例检索
    
    作用：
    1. 从典型案例库中检索相似故障案例
    2. 为诊断和维修提供参考
    
    输入：rewritten_query, item_names, extracted_entities
    输出：case_chunks（案例检索结果）
    """
    add_running_task(state.get("session_id", ""), "node_case_search", state.get("is_stream", False))
    
    try:
        state = search_cases(state)
        logger.info(f"案例检索完成，结果数量：{len(state.get('case_chunks', []))}")
    except Exception as e:
        logger.error(f"案例检索失败：{e}")
        state["case_chunks"] = []
    
    add_done_task(state.get("session_id", ""), "node_case_search", state.get("is_stream", False))
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "rewritten_query": "发动机异响怎么修？",
        "item_names": ["HAK 180 烫金机"],
        "extracted_entities": {
            "fault_symptom": "发动机异响",
        },
        "is_stream": False,
    }
    
    result = node_case_search(mock_state)
    print(f"案例检索结果：{len(result.get('case_chunks', []))} 条")
