# -*- coding: utf-8 -*-
"""查询侧最小链路测试：主体确认 + 关键词检索"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.process.query.agent.state import create_query_default_state
from app.process.query.agent.nodes.node_item_name_confirm import node_item_name_confirm
from app.process.query.agent.nodes.node_keyword_search import node_keyword_search
from app.shared.runtime.logger import logger


def emit(message: str):
    print(message, flush=True)
    logger.info(message)


def test_query_keyword_search_sanbao():
    state = create_query_default_state(
        session_id="test_query_001",
        original_query="三包手册里质保政策是什么？",
        rewritten_query="",
        is_stream=False,
        history=[],
    )

    emit("=" * 60)
    emit("开始 query 最小链路测试：主体确认 + 关键词检索")
    emit("=" * 60)

    state = node_item_name_confirm(state)
    emit(f"识别到主体: {state.get('item_names', [])}")
    emit(f"改写后问题: {state.get('rewritten_query', '')}")

    assert state.get("item_names"), "未识别到 item_names，无法继续关键词检索"
    assert state.get("rewritten_query"), "未生成 rewritten_query"

    keyword_state = node_keyword_search(state)
    keyword_chunks = keyword_state.get("keyword_chunks", [])

    emit(f"关键词召回数量: {len(keyword_chunks)}")
    if keyword_chunks:
        first_chunk = keyword_chunks[0]
        emit(f"首条召回主体: {first_chunk.get('item_name', '')}")
        emit(f"首条召回标题: {first_chunk.get('title', '')}")
        emit(f"首条召回分数: {first_chunk.get('score', 0)}")
        emit(f"首条内容预览: {first_chunk.get('content', '')[:120]}...")

    assert keyword_chunks, "关键词检索未召回任何结果"


def test_query_structured_search_sanbao():
    from app.process.query.agent.nodes.node_structured_query import node_structured_query

    state = create_query_default_state(
        session_id="test_query_structured_001",
        original_query="三包手册质保政策",
        rewritten_query="三包手册 质保政策",
        is_stream=False,
        history=[],
        item_names=["三包手册"],
        extracted_entities={"vehicle_model": "", "doc_type": "质保政策"},
    )

    emit("=" * 60)
    emit("开始结构化查询测试")
    emit("=" * 60)

    result = node_structured_query(state)
    structured_chunks = result.get("structured_chunks", [])

    emit(f"结构化召回数量: {len(structured_chunks)}")
    if structured_chunks:
        first_chunk = structured_chunks[0]
        emit(f"首条召回标题: {first_chunk.get('title', '')}")
        emit(f"首条召回分数: {first_chunk.get('score', 0)}")
        emit(f"首条内容预览: {first_chunk.get('content', '')[:120]}...")

    assert structured_chunks, "结构化查询未召回任何结果"


def test_query_case_search_sanbao():
    from app.process.query.agent.nodes.node_case_search import node_case_search

    state = create_query_default_state(
        session_id="test_query_case_001",
        original_query="三包维修案例",
        rewritten_query="三包 手册 维修 案例 故障 处理",
        is_stream=False,
        history=[],
        item_names=["三包手册"],
    )

    emit("=" * 60)
    emit("开始案例检索测试")
    emit("=" * 60)

    result = node_case_search(state)
    case_chunks = result.get("case_chunks", [])

    emit(f"案例召回数量: {len(case_chunks)}")
    if case_chunks:
        first_chunk = case_chunks[0]
        emit(f"首条召回标题: {first_chunk.get('title', '')}")
        emit(f"首条召回分数: {first_chunk.get('score', 0)}")
        emit(f"首条内容预览: {first_chunk.get('content', '')[:120]}...")

    emit("注意：案例检索依赖文档中包含'案例/故障/维修'等关键词，无命中可能为空")


def test_rrf_fusion_multi_route():
    from app.rag.query.rrf_service import rrf_fusion

    emit("=" * 60)
    emit("开始 RRF 多路融合测试")
    emit("=" * 60)

    embedding_chunks = [
        {"chunk_id": 1001, "content": "质保政策内容A", "title": "质保A", "item_name": "三包手册", "type": "milvus", "score": 0.9},
        {"chunk_id": 1002, "content": "保养周期内容B", "title": "保养B", "item_name": "三包手册", "type": "milvus", "score": 0.8},
        {"chunk_id": 1003, "content": "维修条款内容C", "title": "维修C", "item_name": "三包手册", "type": "milvus", "score": 0.7},
    ]
    keyword_chunks = [
        {"chunk_id": 1002, "content": "保养周期内容B", "title": "保养B", "item_name": "三包手册", "type": "keyword", "score": 5.0},
        {"chunk_id": 1001, "content": "质保政策内容A", "title": "质保A", "item_name": "三包手册", "type": "keyword", "score": 3.0},
        {"chunk_id": 1004, "content": "故障排除内容D", "title": "故障D", "item_name": "三包手册", "type": "keyword", "score": 2.0},
    ]
    structured_chunks = [
        {"chunk_id": "mongo_001", "content": "文档元数据信息", "title": "三包手册", "item_name": "三包手册", "type": "structured", "score": 4.0},
    ]

    weighted_routes = [
        (1.0, embedding_chunks),
        (1.0, keyword_chunks),
        (1.0, structured_chunks),
    ]

    result = rrf_fusion(weighted_routes, limit=5, k=60)

    emit(f"融合前各路: embedding={len(embedding_chunks)}, keyword={len(keyword_chunks)}, structured={len(structured_chunks)}")
    emit(f"融合后结果数: {len(result)}")
    for i, chunk in enumerate(result):
        emit(f"  #{i+1}: chunk_id={chunk.get('chunk_id')}, type={chunk.get('type')}, score={chunk.get('score', 0):.6f}, title={chunk.get('title', '')}")

    assert result, "RRF 融合结果为空"
    assert len(result) <= 5, "RRF 融合结果超出 limit"
    assert result[0]["score"] >= result[-1]["score"], "RRF 融合结果未按分数降序排列"

    emit("RRF 多路融合测试通过")
