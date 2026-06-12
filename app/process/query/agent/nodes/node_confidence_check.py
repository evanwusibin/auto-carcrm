# -*- coding: utf-8 -*-
"""
节点：置信度检查 (node_confidence_check)
作用：检查检索结果的置信度，决定是否需要追问
"""
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.confidence_service import check_confidence


@node_log("node_confidence_check")
def node_confidence_check(state: QueryGraphState) -> QueryGraphState:
    """
    节点：置信度检查
    
    作用：
    1. 检查检索结果的置信度
    2. 如果置信度不足，设置 need_followup=True
    3. 如果置信度足够，继续生成答案
    
    输入：reranked_docs, extracted_entities
    输出：need_followup, followup_question
    """
    add_running_task(state.get("session_id", ""), "node_confidence_check", state.get("is_stream", False))
    
    try:
        state = check_confidence(state)
        logger.info(f"置信度检查完成，置信度：{state.get('confidence_score', 0):.2f}，是否需要追问：{state.get('need_followup', False)}")
    except Exception as e:
        logger.error(f"置信度检查失败：{e}")
        state["need_followup"] = False
        state["confidence_score"] = 0.0
    
    add_done_task(state.get("session_id", ""), "node_confidence_check", state.get("is_stream", False))
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "rewritten_query": "发动机异响怎么修？",
        "reranked_docs": [
            {"chunk_id": "chunk-001", "content": "发动机异响...", "score": 0.95},
        ],
        "extracted_entities": {
            "fault_symptom": "发动机异响",
        },
        "is_stream": False,
    }
    
    result = node_confidence_check(mock_state)
    print(f"置信度：{result.get('confidence_score', 0):.2f}")
    print(f"是否需要追问：{result.get('need_followup', False)}")
