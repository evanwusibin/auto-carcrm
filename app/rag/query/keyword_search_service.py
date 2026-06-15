# -*- coding: utf-8 -*-
"""BM25关键词检索服务"""
from app.infra.vectorstore.milvus_gateway import milvus_gateway
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log


@step_log("validate_keyword_search_state")
def validate_keyword_search_state(state: QueryGraphState):
    item_names = state.get("item_names", [])
    rewritten_query = state.get("rewritten_query", "")
    if not item_names:
        logger.error("item_names not exist")
        raise ValueError("item_names not exist")
    if not rewritten_query:
        logger.error("rewritten_query not exist")
        raise ValueError("rewritten_query not exist")
    return item_names, rewritten_query


@step_log("search_keyword_chunks")
def search_keyword_chunks(rewritten_query: str, item_names: list[str]):
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
        limit=200,
    )

    query_terms = {term for term in rewritten_query.lower().split() if term.strip()}
    if not query_terms:
        return []

    scored_chunks = []
    for row in result or []:
        content = str(row.get("content", ""))
        title = str(row.get("title", ""))
        parent_title = str(row.get("parent_title", ""))
        search_text = f"{title} {parent_title} {content}".lower()
        score = sum(search_text.count(term) for term in query_terms)
        if score <= 0:
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
                "type": "keyword",
                "url": None,
            }
        )

    scored_chunks.sort(key=lambda chunk: chunk["score"], reverse=True)
    return scored_chunks[:10]


@step_log("search_by_keywords")
def search_by_keywords(state: QueryGraphState) -> QueryGraphState:
    logger.info("[keyword_search] BM25关键词检索开始")
    # milvus检索就直接存到state中了
    item_names, rewritten_query = validate_keyword_search_state(state)
    state["keyword_chunks"] = search_keyword_chunks(rewritten_query, item_names)
    logger.info(f"[keyword_search] BM25关键词检索完成，召回 {len(state['keyword_chunks'])} 条")
    return state
