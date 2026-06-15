# -*- coding: utf-8 -*-
"""置信度处理服务"""
from app.shared.runtime.logger import logger


def check_confidence(state: dict) -> dict:
    """计算检索结果的置信度，决定是否需要追问"""
    logger.info("[confidence] 置信度判断开始")
    
    rrf_chunks = state.get("rrf_chunks", [])
    item_names = state.get("item_names", [])
    
    # 计算平均分数
    scores = [chunk.get("score", 0) for chunk in rrf_chunks[:3]]
    avg_score = sum(scores) / max(len(scores), 1) if scores else 0
    
    # 是否有主体
    has_item = len(item_names) > 0
    
    # 计算置信度
    confidence = avg_score * 0.8 + (0.2 if has_item else 0)
    
    # 判断是否需要追问
    need_followup = confidence < 0.6
    
    state["confidence_score"] = round(confidence, 2)
    state["need_followup"] = need_followup
    
    if need_followup:
        state["followup_question"] = "请问您具体是哪款车型？或者能提供更多故障信息吗？"
    
    logger.info(f"[confidence] 置信度={confidence:.2f}, 需要追问={need_followup}")
    return state
