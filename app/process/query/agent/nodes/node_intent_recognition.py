# -*- coding: utf-8 -*-
"""
节点：意图识别 (node_intent_recognition)
作用：分析用户问题，识别查询意图类型
"""
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.intent_recognition_service import recognize_intent


@node_log("node_intent_recognition")
def node_intent_recognition(state: QueryGraphState) -> QueryGraphState:
    """
    节点：意图识别
    
    作用：
    1. 分析用户问题，识别查询意图类型
    2. 根据意图决定后续检索策略
    
    意图类型：
    - pre_sales_consultation：售前咨询（产品参数、价格、配置）
    - after_sales_service：售后服务（维修、保养、故障）
    - vehicle_usage_guide：用车指导（操作方法、注意事项）
    - complaint_emotion：投诉/情绪类（需要安抚）
    - business_transaction：业务办理（报修、预约）
    - general_chat：闲聊寒暄
    
    输入：rewritten_query, item_names
    输出：intent（意图类型）
    """
    add_running_task(state.get("session_id", ""), "node_intent_recognition", state.get("is_stream", False))
    
    try:
        # 调用意图识别服务
        state = recognize_intent(state)
        logger.info(f"意图识别完成，意图类型：{state.get('intent', 'unknown')}")
    except Exception as e:
        logger.error(f"意图识别失败：{e}")
        # 默认设为售后服务意图
        state["intent"] = "after_sales_service"
    
    add_done_task(state.get("session_id", ""), "node_intent_recognition", state.get("is_stream", False))
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "original_query": "烫金机怎么用？",
        "rewritten_query": "烫金机的使用方法是什么？",
        "item_names": ["HAK 180 烫金机"],
        "is_stream": False,
    }
    
    result = node_intent_recognition(mock_state)
    print(f"意图类型：{result.get('intent')}")
