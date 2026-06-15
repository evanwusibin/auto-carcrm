# -*- coding: utf-8 -*-
"""案例检索服务"""
from app.infra.vectorstore.milvus_gateway import milvus_gateway
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log


@step_log("validate_case_search_state")
def validate_case_search_state(state: QueryGraphState):
    item_names = state.get("item_names", [])
    rewritten_query = state.get("rewritten_query", "")
    if not item_names:
        logger.error("item_names not exist")
        raise ValueError("item_names not exist")
    if not rewritten_query:
        logger.error("rewritten_query not exist")
        raise ValueError("rewritten_query not exist")
    return item_names, rewritten_query


@step_log("search_case_chunks")
def search_case_chunks(item_names: list[str], rewritten_query: str):
    result = milvus_gateway.client.query(
        collection_name=milvus_gateway.chunk_collection_name,
        filter=f"item_name in {item_names}",
        output_fields=[
            "chunk_id",
            "item_name",
            "parent_title",
            "part",
            "title",
            "file_title",
            "content",
        ],
        limit=300,
    )

    case_terms = ["案例", "故障", "维修", "处理", "现象", "原因", "解决", "排查"]
    query_terms = {term for term in rewritten_query.lower().split() if term.strip()}
    scored_chunks = []

    for row in result or []:
        content = str(row.get("content", ""))
        title = str(row.get("title", ""))
        parent_title = str(row.get("parent_title", ""))
        search_text = f"{title} {parent_title} {content}".lower()
        score = sum(search_text.count(term) for term in query_terms)
        case_boost = sum(search_text.count(term) for term in case_terms)
        score += case_boost * 1.5
        if score <= 0 or case_boost <= 0:
            continue

        scored_chunks.append(
            {
                "chunk_id": row.get("chunk_id"),
                "item_name": row.get("item_name", ""),
                "title": row.get("title"),
                "parent_title": row.get("parent_title"),
                "part": row.get("part"),
                "file_title": row.get("file_title"),
                "content": row.get("content", ""),
                "score": float(score),
                "type": "case",
                "url": None,
            }
        )

    scored_chunks.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    return scored_chunks[:5]


@step_log("search_cases")
def search_cases(state: QueryGraphState) -> QueryGraphState:
    logger.info("[case_search] 案例检索开始")
    item_names, rewritten_query = validate_case_search_state(state)
    state["case_chunks"] = search_case_chunks(item_names, rewritten_query)
    logger.info(f"[case_search] 案例检索完成，召回 {len(state['case_chunks'])} 条")
    return state
