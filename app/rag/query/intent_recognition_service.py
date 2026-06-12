# -*- coding: utf-8 -*-
"""
意图识别服务
作用：调用 LLM 分析用户问题，识别查询意图类型
"""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.infra.llm.providers import llm_provider
from app.shared.runtime.load_prompt import load_prompt
from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState


# 意图类型枚举
INTENT_TYPES = {
    "pre_sales_consultation": "售前咨询（产品参数、价格、配置）",
    "after_sales_service": "售后服务（维修、保养、故障）",
    "vehicle_usage_guide": "用车指导（操作方法、注意事项）",
    "complaint_emotion": "投诉/情绪类（需要安抚）",
    "business_transaction": "业务办理（报修、预约）",
    "general_chat": "闲聊寒暄",
}


@step_log("validate_intent_state")
def validate_intent_state(state: QueryGraphState):
    """校验意图识别所需参数"""
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        raise ValueError("rewritten_query 为空，无法进行意图识别")
    return rewritten_query


@step_log("call_llm_recognize_intent")
def call_llm_recognize_intent(rewritten_query: str) -> str:
    """
    调用 LLM 识别意图
    
    输入：rewritten_query（重写后的问题）
    输出：intent_type（意图类型字符串）
    """
    # 获取 LLM 客户端
    llm_client = llm_provider.chat()
    
    # 加载提示词
    prompt_text = load_prompt("intent_recognition", rewritten_query=rewritten_query)
    
    # 构建消息
    messages = [
        SystemMessage(content="你是一个意图识别专家，负责分析用户问题的意图类型。"),
        HumanMessage(content=prompt_text),
    ]
    
    # 调用链
    chains = llm_client | StrOutputParser()
    intent_type = chains.invoke(messages)
    
    return intent_type.strip().lower()


def recognize_intent(state: QueryGraphState) -> QueryGraphState:
    """
    意图识别主函数
    
    输入：state（包含 rewritten_query）
    输出：state（新增 intent 字段）
    """
    # 1. 校验参数
    rewritten_query = validate_intent_state(state)
    
    # 2. 调用 LLM 识别意图
    intent_type = call_llm_recognize_intent(rewritten_query)
    
    # 3. 校验意图类型是否有效
    if intent_type not in INTENT_TYPES:
        logger.warning(f"识别到未知意图类型：{intent_type}，默认设为 after_sales_service")
        intent_type = "after_sales_service"
    
    # 4. 写入 state
    state["intent"] = intent_type
    
    logger.info(f"意图识别完成：{rewritten_query} → {intent_type}（{INTENT_TYPES[intent_type]}）")
    
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "rewritten_query": "烫金机的使用方法是什么？",
    }
    
    result = recognize_intent(mock_state)
    print(f"意图类型：{result.get('intent')}")
