# -*- coding: utf-8 -*-
"""结构化查询服务"""
from app.infra.persistence.knowledge_repository import knowledge_repository
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log


@step_log("validate_structured_query_state")
def validate_structured_query_state(state: QueryGraphState):
    item_names = state.get("item_names", [])
    rewritten_query = state.get("rewritten_query", "")
    extracted_entities = state.get("extracted_entities", {}) or {}
    if not item_names:
        logger.error("item_names not exist")
        raise ValueError("item_names not exist")
    if not rewritten_query:
        logger.error("rewritten_query not exist")
        raise ValueError("rewritten_query not exist")
    return item_names, rewritten_query, extracted_entities


@step_log("search_structured_documents")
def search_structured_documents(item_names: list[str], rewritten_query: str, extracted_entities: dict):
    query_terms = {term for term in rewritten_query.lower().split() if term.strip()}
    vehicle_model = str(extracted_entities.get("vehicle_model") or extracted_entities.get("model") or "").strip()
    doc_type = str(extracted_entities.get("doc_type") or extracted_entities.get("document_type") or "").strip()

    documents = []
    for item_name in item_names:
        documents.extend(knowledge_repository.find_by_item_name(item_name))

    structured_chunks = []
    for document in documents:
        content_parts = [
            str(document.get("title", "")),
            str(document.get("item_name", "")),
            str(document.get("vehicle_model", "")),
            str(document.get("version", "")),
            str(document.get("doc_type", "")),
            " ".join(str(tag) for tag in document.get("tags", [])),
        ]
        search_text = " ".join(content_parts).lower()
        score = sum(search_text.count(term) for term in query_terms)
        if vehicle_model and vehicle_model.lower() and vehicle_model.lower() in search_text:
            score += 2
        if doc_type and doc_type.lower() and doc_type.lower() in search_text:
            score += 2
        if score <= 0:
            continue

        structured_chunks.append(
            {
                "chunk_id": str(document.get("_id")),
                "item_name": document.get("item_name", ""),
                "title": document.get("title", ""),
                "parent_title": "知识文档元数据",
                "part": 0,
                "file_title": document.get("title", ""),
                "content": (
                    f"文档名称：{document.get('title', '')}\n"
                    f"主体名称：{document.get('item_name', '')}\n"
                    f"车型：{document.get('vehicle_model', '')}\n"
                    f"版本：{document.get('version', '')}\n"
                    f"文档类型：{document.get('doc_type', '')}\n"
                    f"状态：{document.get('status', '')}\n"
                    f"标签：{', '.join(document.get('tags', [])) if document.get('tags') else '无'}"
                ),
                "score": float(score),
                "type": "structured",
                "url": None,
            }
        )

    structured_chunks.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    return structured_chunks[:5]


@step_log("query_structured_data")
def query_structured_data(state: QueryGraphState) -> QueryGraphState:
    logger.info("[structured_query] 结构化查询开始")
    item_names, rewritten_query, extracted_entities = validate_structured_query_state(state)
    state["structured_chunks"] = search_structured_documents(item_names, rewritten_query, extracted_entities)
    logger.info(f"[structured_query] 结构化查询完成，召回 {len(state['structured_chunks'])} 条")
    return state
