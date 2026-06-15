# -*- coding: utf-8 -*-
"""
RRF (Reciprocal Rank Fusion) 融合服务
作用：将 6 路召回结果进行加权融合排序
"""
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log


RRF_K = 60
RRF_LIMIT = 10


@step_log("get_data_and_validate")
def get_data_and_validate(state):
    embedding_chunks = state.get("embedding_chunks", []) or []
    hyde_embedding_chunks = state.get("hyde_embedding_chunks", []) or []
    keyword_chunks = state.get("keyword_chunks", []) or []
    structured_chunks = state.get("structured_chunks", []) or []
    case_chunks = state.get("case_chunks", []) or []

    total = (
        len(embedding_chunks)
        + len(hyde_embedding_chunks)
        + len(keyword_chunks)
        + len(structured_chunks)
        + len(case_chunks)
    )
    if total == 0:
        logger.error("所有召回路结果均为空，无法继续 RRF 融合")
        raise ValueError("所有召回路结果均为空，无法继续 RRF 融合")

    return {
        "embedding_chunks": embedding_chunks,
        "hyde_embedding_chunks": hyde_embedding_chunks,
        "keyword_chunks": keyword_chunks,
        "structured_chunks": structured_chunks,
        "case_chunks": case_chunks,
    }


@step_log("rrf_fusion")
def rrf_fusion(chunks_list: list[tuple[float, list]], limit: int, k: int = RRF_K):
    score_dict: dict[str, float] = {}
    chunk_dict: dict[str, dict] = {}

    for weight, current_chunks in chunks_list:
        for rank, chunk in enumerate(current_chunks, start=1):
            chunk_id = chunk.get("chunk_id")
            if chunk_id is None:
                continue
            chunk_key = str(chunk_id)
            score_dict[chunk_key] = score_dict.get(chunk_key, 0) + weight * (1 / (k + rank))
            chunk_dict.setdefault(chunk_key, chunk)

    chunk_list = []
    for chunk_key, score in score_dict.items():
        chunk = chunk_dict[chunk_key]
        chunk["score"] = score
        chunk_list.append(chunk)

    chunk_list.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    return chunk_list[:limit]


@step_log("fuse_by_rrf")
def fuse_by_rrf(state: QueryGraphState) -> QueryGraphState:
    """
    RRF 融合服务：
    1. 从 state 中获取全部 6 路召回结果
    2. 只融合非空的路，避免空列表拖垮融合
    3. 应用 RRF 算法消除分数差异
    4. 回写 rrf_chunks
    """
    route_data = get_data_and_validate(state)

    # 组合元祖列表
    weighted_routes = [
        (1.0, route_data["embedding_chunks"]),
        (1.0, route_data["hyde_embedding_chunks"]),
        (1.0, route_data["keyword_chunks"]),
        (1.0, route_data["structured_chunks"]),
        (1.0, route_data["case_chunks"]),
    ]

    non_empty_routes = [(w, chunks) for w, chunks in weighted_routes if chunks]
    logger.info(f"[RRF] 参与融合的召回路数: {len(non_empty_routes)}/{len(weighted_routes)}")
    for i, (w, chunks) in enumerate(non_empty_routes):
        logger.info(f"[RRF] 路径 {i}: 权重={w}, 候选数={len(chunks)}")

    rrf_chunks = rrf_fusion(non_empty_routes, limit=RRF_LIMIT, k=RRF_K)
    logger.info(f"[RRF] 融合完成，输出 {len(rrf_chunks)} 条")
    state["rrf_chunks"] = rrf_chunks
    return state
