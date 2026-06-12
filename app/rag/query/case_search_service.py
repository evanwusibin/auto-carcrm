# -*- coding: utf-8 -*-
"""
案例检索服务
作用：从典型案例库中检索相似故障案例
"""
from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState


@step_log("validate_case_state")
def validate_case_state(state: QueryGraphState):
    """校验案例检索所需参数"""
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        raise ValueError("rewritten_query 为空，无法进行案例检索")
    return rewritten_query


def search_cases(state: QueryGraphState) -> QueryGraphState:
    """
    案例检索主函数
    
    输入：state（包含 rewritten_query, extracted_entities）
    输出：state（新增 case_chunks 字段）
    """
    # 1. 校验参数
    rewritten_query = validate_case_state(state)
    
    # 2. 提取实体
    entities = state.get("extracted_entities", {})
    fault_symptom = entities.get("fault_symptom", "")
    
    # 3. TODO: 从 Milvus kb_cases 集合中检索相似案例
    # 暂时返回空列表
    case_chunks = []
    
    # 4. 写入 state
    state["case_chunks"] = case_chunks
    
    logger.info(f"案例检索完成：{rewritten_query} → {len(case_chunks)} 条结果")
    
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "rewritten_query": "发动机异响怎么修？",
        "extracted_entities": {
            "fault_symptom": "发动机异响",
        },
    }
    
    result = search_cases(mock_state)
    print(f"案例检索结果：{len(result.get('case_chunks', []))} 条")
