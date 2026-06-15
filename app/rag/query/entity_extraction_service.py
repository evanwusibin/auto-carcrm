# -*- coding: utf-8 -*-
"""
实体抽取服务
作用：调用 LLM 从用户问题中提取关键实体信息
参考老师 answer_service.py 的代码风格
"""
import json
from langchain_core.messages import HumanMessage

from app.infra.llm.providers import llm_provider
from app.shared.runtime.load_prompt import load_prompt
from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState


# 实体类型定义
ENTITY_TYPES = {
    "vehicle_model": "车型（如 T5、T7）",
    "vin": "车架号（VIN码）",
    "fault_code": "故障码（如 P0A0F）",
    "mileage": "行驶里程",
    "component": "部件（如 发动机、电池）",
    "purchase_date": "购车日期",
    "fault_symptom": "故障现象描述",
    "doc_type": "文档类型（如质保政策、保养手册、维修手册、案例）",
}


@step_log("validate_entity_state")
def validate_entity_state(state: QueryGraphState):
    """校验实体抽取所需参数"""
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        logger.error("rewritten_query 为空，无法进行实体抽取")
        raise ValueError("rewritten_query 为空，无法进行实体抽取")
    return rewritten_query


def extract_entities(state: QueryGraphState) -> QueryGraphState:
    """
    实体抽取主函数（参考老师 answer_service.py 风格）
    
    输入：state（包含 rewritten_query）
    输出：state（新增 extracted_entities 字段）
    """
    # 1. 校验参数
    rewritten_query = validate_entity_state(state)
    
    # 2. 获取 LLM 客户端
    llm_client = llm_provider.chat()
    
    # 3. 加载提示词
    prompt_text = load_prompt("entity_extraction", query=rewritten_query)
    
    # 4. 构建消息
    messages = [HumanMessage(content=prompt_text)]
    
    # 5. 调用 LLM
    response = llm_client.invoke(messages)
    result_text = response.content.strip()
    
    # 6. 解析 JSON 结果
    try:
        entities = json.loads(result_text)
    except json.JSONDecodeError:
        logger.warning(f"实体抽取结果解析失败：{result_text}")
        entities = {}
    
    # 7. 校验实体类型，只保留有效实体
    valid_entities = {}
    for key, value in entities.items():
        if key in ENTITY_TYPES and value:
            valid_entities[key] = value
    
    # 8. 写入 state
    state["extracted_entities"] = valid_entities
    
    logger.info(f"实体抽取完成：{rewritten_query} → {valid_entities}")
    
    return state
