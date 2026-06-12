# -*- coding: utf-8 -*-
"""
元数据过滤服务
作用：按车型/版本/有效期/权限过滤检索结果
参考老师 answer_service.py 的代码风格
"""
from datetime import datetime

from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState


@step_log("validate_filter_state")
def validate_filter_state(state: QueryGraphState):
    """校验元数据过滤所需参数"""
    rrf_chunks = state.get("rrf_chunks", [])
    return rrf_chunks


def filter_by_vehicle_model(chunks: list[dict], vehicle_model: str) -> list[dict]:
    """
    按车型过滤
    
    输入：chunks（检索结果列表），vehicle_model（车型）
    输出：filtered_chunks（过滤后的结果）
    """
    if not vehicle_model:
        return chunks
    
    filtered_chunks = []
    for chunk in chunks:
        chunk_vehicle_model = chunk.get("vehicle_model", "")
        # 如果 chunk 没有车型信息，或者车型匹配，则保留
        if not chunk_vehicle_model or chunk_vehicle_model == vehicle_model:
            filtered_chunks.append(chunk)
    
    return filtered_chunks


def filter_by_expire_date(chunks: list[dict]) -> list[dict]:
    """
    按有效期过滤（过滤掉已过期的文档）
    
    输入：chunks（检索结果列表）
    输出：filtered_chunks（过滤后的结果）
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    filtered_chunks = []
    for chunk in chunks:
        expire_date = chunk.get("expire_date", "")
        # 如果没有过期日期，或者过期日期大于今天，则保留
        if not expire_date or expire_date >= today:
            filtered_chunks.append(chunk)
    
    return filtered_chunks


def filter_by_visible_roles(chunks: list[dict], user_role: str) -> list[dict]:
    """
    按权限过滤
    
    输入：chunks（检索结果列表），user_role（用户角色）
    输出：filtered_chunks（过滤后的结果）
    """
    if not user_role:
        return chunks
    
    filtered_chunks = []
    for chunk in chunks:
        visible_roles = chunk.get("visible_roles", [])
        # 如果没有权限限制，或者用户角色在可见角色列表中，则保留
        if not visible_roles or user_role in visible_roles:
            filtered_chunks.append(chunk)
    
    return filtered_chunks


def filter_by_state(chunks: list[dict]) -> list[dict]:
    """
    按状态过滤（只保留 active 状态的文档）
    
    输入：chunks（检索结果列表）
    输出：filtered_chunks（过滤后的结果）
    """
    filtered_chunks = []
    for chunk in chunks:
        state = chunk.get("state", "active")
        # 如果没有状态信息，或者状态为 active，则保留
        if not state or state == "active":
            filtered_chunks.append(chunk)
    
    return filtered_chunks


def apply_metadata_filter(state: QueryGraphState) -> QueryGraphState:
    """
    元数据过滤主函数（参考老师 answer_service.py 风格）
    
    输入：state（包含 rrf_chunks, extracted_entities）
    输出：state（更新 rrf_chunks 字段）
    """
    # 1. 校验参数
    rrf_chunks = validate_filter_state(state)
    
    # 2. 提取过滤条件
    entities = state.get("extracted_entities", {})
    vehicle_model = entities.get("vehicle_model", "")
    user_role = state.get("user_role", "")
    
    # 3. 按车型过滤
    filtered_chunks = filter_by_vehicle_model(rrf_chunks, vehicle_model)
    logger.info(f"车型过滤后：{len(rrf_chunks)} → {len(filtered_chunks)} 条")
    
    # 4. 按有效期过滤
    filtered_chunks = filter_by_expire_date(filtered_chunks)
    logger.info(f"有效期过滤后：{len(filtered_chunks)} 条")
    
    # 5. 按权限过滤
    filtered_chunks = filter_by_visible_roles(filtered_chunks, user_role)
    logger.info(f"权限过滤后：{len(filtered_chunks)} 条")
    
    # 6. 按状态过滤
    filtered_chunks = filter_by_state(filtered_chunks)
    logger.info(f"状态过滤后：{len(filtered_chunks)} 条")
    
    # 7. 写入 state
    state["rrf_chunks"] = filtered_chunks
    
    logger.info(f"元数据过滤完成：{len(rrf_chunks)} → {len(filtered_chunks)} 条")
    
    return state
