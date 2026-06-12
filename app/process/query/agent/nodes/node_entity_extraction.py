# -*- coding: utf-8 -*-
"""
节点：实体抽取 (node_entity_extraction)
作用：从用户问题中提取关键实体信息
"""
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.entity_extraction_service import extract_entities


@node_log("node_entity_extraction")
def node_entity_extraction(state: QueryGraphState) -> QueryGraphState:
    """
    节点：实体抽取
    
    作用：
    1. 从用户问题中提取关键实体信息
    2. 为后续检索提供过滤条件
    
    实体类型：
    - vehicle_model：车型（如 T5、T7）
    - vin：车架号（VIN码）
    - fault_codes：故障码（如 P0A0F）
    - mileage：行驶里程
    - component：部件（如 发动机、电池）
    - purchase_date：购车日期
    - fault_symptom：故障现象描述
    
    输入：rewritten_query, item_names
    输出：extracted_entities（实体字典）
    """
    add_running_task(state.get("session_id", ""), "node_entity_extraction", state.get("is_stream", False))
    
    try:
        state = extract_entities(state)
        logger.info(f"实体抽取完成，实体：{state.get('extracted_entities', {})}")
    except Exception as e:
        logger.error(f"实体抽取失败：{e}")
        state["extracted_entities"] = {}
    
    add_done_task(state.get("session_id", ""), "node_entity_extraction", state.get("is_stream", False))
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "original_query": "我的T5车架号是LVSHFFAN5MF123456，发动机异响怎么办？",
        "rewritten_query": "T5车型车架号LVSHFFAN5MF123456发动机异响的解决方法",
        "item_names": ["HAK 180 烫金机"],
        "is_stream": False,
    }
    
    result = node_entity_extraction(mock_state)
    print(f"实体：{result.get('extracted_entities')}")
