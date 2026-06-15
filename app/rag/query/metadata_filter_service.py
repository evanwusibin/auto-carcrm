# -*- coding: utf-8 -*-
"""元数据过滤服务"""
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log


@step_log("filter_by_metadata")
def filter_by_metadata(state: QueryGraphState) -> QueryGraphState:
    """
    对 RRF 融合后的结果做元数据过滤：
    1. 从 extracted_entities 中提取过滤条件
    2. 对 rrf_chunks 中的每条结果检查是否匹配
    3. 保留匹配的结果，不匹配的降权但不丢弃
    4. 回写 filtered_chunks
    """
    logger.info("[metadata_filter] 元数据过滤开始")

    rrf_chunks = state.get("rrf_chunks", []) or []
    extracted_entities = state.get("extracted_entities", {}) or {}

    if not rrf_chunks:
        logger.warning("[metadata_filter] rrf_chunks 为空，跳过过滤")
        state["filtered_chunks"] = []
        return state

    vehicle_model = str(extracted_entities.get("vehicle_model") or extracted_entities.get("model") or "").strip().lower()
    doc_type = str(extracted_entities.get("doc_type") or extracted_entities.get("document_type") or "").strip().lower()

    if not vehicle_model and not doc_type:
        logger.info("[metadata_filter] 无过滤条件，直接透传")
        state["filtered_chunks"] = rrf_chunks
        return state

    filtered = []
    demoted = []

    for chunk in rrf_chunks:
        content = str(chunk.get("content", "")).lower()
        title = str(chunk.get("title", "")).lower()
        parent_title = str(chunk.get("parent_title", "")).lower()
        search_text = f"{content} {title} {parent_title}"

        match = True
        if vehicle_model and vehicle_model not in search_text:
            match = False
        if doc_type and doc_type not in search_text:
            match = False

        if match:
            filtered.append(chunk)
        else:
            chunk_copy = dict(chunk)
            chunk_copy["score"] = chunk_copy.get("score", 0.0) * 0.5
            demoted.append(chunk_copy)

    if filtered:
        result = sorted(filtered, key=lambda x: x.get("score", 0.0), reverse=True)
        logger.info(f"[metadata_filter] 匹配 {len(filtered)} 条，降权 {len(demoted)} 条")
    else:
        result = sorted(rrf_chunks, key=lambda x: x.get("score", 0.0), reverse=True)
        logger.info("[metadata_filter] 无完全匹配，保留全部原始结果")

    state["filtered_chunks"] = result
    return state
