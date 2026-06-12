# -*- coding: utf-8 -*-
"""
置信度检查服务
作用：检查检索结果的置信度，决定是否需要追问
参考老师 answer_service.py 的代码风格
"""
from app.shared.runtime.logger import logger, step_log
from app.shared.config.rag_config import rag_config
from app.process.query.agent.state import QueryGraphState


@step_log("validate_confidence_state")
def validate_confidence_state(state: QueryGraphState):
    """校验置信度检查所需参数"""
    reranked_docs = state.get("reranked_docs", [])
    return reranked_docs


def calculate_confidence_score(reranked_docs: list[dict]) -> float:
    """
    计算置信度分数
    
    输入：reranked_docs（重排序后的文档列表）
    输出：confidence_score（置信度分数，0-1）
    """
    if not reranked_docs:
        return 0.0
    
    # 取 Top-1 分数作为置信度
    top_score = reranked_docs[0].get("score", 0.0)
    
    return top_score


def determine_followup_need(confidence_score: float, entities: dict) -> tuple[bool, str]:
    """
    判断是否需要追问
    
    输入：confidence_score（置信度分数），entities（实体字典）
    输出：need_followup（是否需要追问），followup_question（追问问题）
    """
    threshold = rag_config.confidence_threshold
    
    # 如果置信度足够，不需要追问
    if confidence_score >= threshold:
        return False, ""
    
    # 如果置信度不足，分析原因并生成追问问题
    if not entities.get("vehicle_model"):
        return True, "请告诉我您的车型，以便我提供更准确的信息。"
    
    if not entities.get("fault_symptom"):
        return True, "请描述一下具体的故障现象，以便我更好地帮助您。"
    
    if not entities.get("mileage"):
        return True, "请告诉我当前的行驶里程，以便我判断保养周期。"
    
    # 默认追问
    return True, "抱歉，我没有找到足够的信息来回答您的问题。请提供更多细节，或者联系授权服务站咨询。"


def check_confidence(state: QueryGraphState) -> QueryGraphState:
    """
    置信度检查主函数（参考老师 answer_service.py 风格）
    
    输入：state（包含 reranked_docs, extracted_entities）
    输出：state（新增 confidence_score, need_followup, followup_question）
    """
    # 1. 校验参数
    reranked_docs = validate_confidence_state(state)
    
    # 2. 计算置信度分数
    confidence_score = calculate_confidence_score(reranked_docs)
    
    # 3. 判断是否需要追问
    entities = state.get("extracted_entities", {})
    need_followup, followup_question = determine_followup_need(confidence_score, entities)
    
    # 4. 写入 state
    state["confidence_score"] = confidence_score
    state["need_followup"] = need_followup
    state["followup_question"] = followup_question
    
    logger.info(f"置信度检查完成：分数={confidence_score:.2f}，阈值={rag_config.confidence_threshold}，需要追问={need_followup}")
    
    return state
