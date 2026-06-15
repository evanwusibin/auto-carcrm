# -*- coding: utf-8 -*-
"""Query 主链路端到端测试"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.process.query.agent.main_graph import query_graph_app
from app.process.query.agent.state import create_query_default_state
from app.shared.runtime.logger import logger


def emit(message: str):
    print(message, flush=True)
    logger.info(message)


def test_query_pipeline_sanbao():
    state = create_query_default_state(
        session_id="test_query_pipeline_001",
        original_query="三包手册里质保政策是什么？",
        rewritten_query="",
        is_stream=False,
        history=[],
    )

    emit("=" * 60)
    emit("开始 Query 主链路端到端测试")
    emit("=" * 60)

    final_state = None
    step_count = 0

    stream_iter = query_graph_app.stream(state, stream_mode="values")
    emit("Query LangGraph stream 已创建，开始迭代")

    for step in stream_iter:
        step_count += 1
        if isinstance(step, dict):
            final_state = step
            keys = list(step.keys())
            emit(f"节点 {step_count} 执行完成，当前 state keys: {keys}")
            if step.get("item_names"):
                emit(f"  item_names: {step.get('item_names')}")
            if step.get("rewritten_query"):
                emit(f"  rewritten_query: {step.get('rewritten_query')}")
            if step.get("rrf_chunks"):
                emit(f"  rrf_chunks: {len(step.get('rrf_chunks', []))}")
            if step.get("filtered_chunks"):
                emit(f"  filtered_chunks: {len(step.get('filtered_chunks', []))}")
            if step.get("reranked_docs"):
                emit(f"  reranked_docs: {len(step.get('reranked_docs', []))}")
            if step.get("confidence_score"):
                emit(f"  confidence_score: {step.get('confidence_score')}")
            if step.get("answer"):
                emit(f"  answer预览: {step.get('answer', '')[:120]}...")

    assert final_state is not None, "Query 主链路没有产出最终 state"
    assert final_state.get("item_names") or final_state.get("answer"), "主体确认阶段未产出有效结果"
    assert step_count > 0, "Query 主链路没有执行任何节点"

    emit("=" * 60)
    emit("Query 主链路测试完成")
    emit(f"总节点步数: {step_count}")
    emit(f"最终主体: {final_state.get('item_names', [])}")
    emit(f"最终置信度: {final_state.get('confidence_score', 0)}")
    emit(f"最终答案预览: {final_state.get('answer', '')[:200]}...")
