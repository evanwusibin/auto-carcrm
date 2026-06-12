# -*- coding: utf-8 -*-
"""
实体抽取服务
作用：调用 LLM 从用户问题中提取关键实体信息
"""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.infra.llm.providers import llm_provider
from app.shared.runtime.load_prompt import load_prompt
from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState


# 实体类型定义
ENTITY_TYPES = {
    "vehicle_model": "车型（如 T5、T7）",
    "vin": "车架号（VIN码）",
    "fault_codes": "故障码（如 P0A0F）",
    "mileage": "行驶里程",
    "component": "部件（如 发动机、电池）",
    "purchase_date": "购车日期",
    "fault_symptom": "故障现象描述",
}


@step_log("validate_entity_state")
def validate_entity_state(state: QueryGraphState):
    """校验实体抽取所需参数"""
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        raise ValueError("rewritten_query 为空，无法进行实体抽取")
    return rewritten_query


@step_log("call_llm_extract_entities")
def call_llm_extract_entities(rewritten_query: str) -> dict:
    """
    调用 LLM 抽取实体
    
    输入：rewritten_query（重写后的问题）
    输出：entities（实体字典）
    """
    # 获取 LLM 客户端
    llm_client = llm_provider.chat()
    
    # 加载提示词
    prompt_text = load_prompt("entity_extraction", rewritten_query=rewritten_query)
    
    # 构建消息
    messages = [
        SystemMessage(content="你是一个实体抽取专家，负责从用户问题中提取关键实体信息。"),
        HumanMessage(content=prompt_text),
    ]
    
    # 调用链
    chains = llm_client | StrOutputParser()
    result = chains.invoke(messages)
    
    # 解析 JSON 结果
    try:
        import json
        entities = json.loads(result)
    except json.JSONDecodeError:
        logger.warning(f"实体抽取结果解析失败：{result}")
        entities = {}
    
    return entities


def extract_entities(state: QueryGraphState) -> QueryGraphState:
    """
    实体抽取主函数
    
    输入：state（包含 rewritten_query）
    输出：state（新增 extracted_entities 字段）
    """
    # 1. 校验参数
    rewritten_query = validate_entity_state(state)
    
    # 2. 调用 LLM 抽取实体
    entities = call_llm_extract_entities(rewritten_query)
    
    # 3. 校验实体类型
    valid_entities = {}
    for key, value in entities.items():
        if key in ENTITY_TYPES and value:
            valid_entities[key] = value
    
    # 4. 写入 state
    state["extracted_entities"] = valid_entities
    
    logger.info(f"实体抽取完成：{rewritten_query} → {valid_entities}")
    
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "rewritten_query": "T5车型车架号LVSHFFAN5MF123456发动机异响的解决方法",
    }
    
    result = extract_entities(mock_state)
    print(f"实体：{result.get('extracted_entities')}")
