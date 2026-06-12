# -*- coding: utf-8 -*-
"""
节点：结构化查询 (node_structured_query)
作用：查询车辆档案、保养记录、质保规则等结构化数据
"""
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.structured_query_service import query_structured_data


@node_log("node_structured_query")
def node_structured_query(state: QueryGraphState) -> QueryGraphState:
    """
    节点：结构化查询
    
    作用：
    1. 查询车辆档案（车型、VIN、里程等）
    2. 查询保养记录
    3. 查询质保规则
    
    输入：rewritten_query, item_names, extracted_entities
    输出：structured_chunks（结构化查询结果）
    """
    add_running_task(state.get("session_id", ""), "node_structured_query", state.get("is_stream", False))
    
    try:
        state = query_structured_data(state)
        logger.info(f"结构化查询完成，结果数量：{len(state.get('structured_chunks', []))}")
    except Exception as e:
        logger.error(f"结构化查询失败：{e}")
        state["structured_chunks"] = []
    
    add_done_task(state.get("session_id", ""), "node_structured_query", state.get("is_stream", False))
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "rewritten_query": "我的T5还在保修期内吗？",
        "item_names": ["HAK 180 烫金机"],
        "extracted_entities": {
            "vehicle_model": "T5",
            "vin": "LVSHFFAN5MF123456",
        },
        "is_stream": False,
    }
    
    result = node_structured_query(mock_state)
    print(f"结构化查询结果：{len(result.get('structured_chunks', []))} 条")
