# -*- coding: utf-8 -*-
"""
节点：QA保存 (node_save_qa)
作用：保存问答会话、消息和引用到 MongoDB
"""
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.qa_persist_service import save_qa_session


@node_log("node_save_qa")
def node_save_qa(state: QueryGraphState) -> QueryGraphState:
    """
    节点：QA保存
    
    作用：
    1. 保存问答会话到 qa_sessions 集合
    2. 保存用户消息到 qa_messages 集合
    3. 保存助手回答到 qa_messages 集合
    4. 保存引用来源到 qa_references 集合
    
    输入：session_id, original_query, answer, image_urls, references
    输出：无（写入 MongoDB）
    """
    add_running_task(state.get("session_id", ""), "node_save_qa", state.get("is_stream", False))
    
    try:
        save_qa_session(state)
        logger.info("QA保存完成")
    except Exception as e:
        logger.error(f"QA保存失败：{e}")
    
    add_done_task(state.get("session_id", ""), "node_save_qa", state.get("is_stream", False))
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "original_query": "发动机异响怎么修？",
        "answer": "发动机异响可能是由于...",
        "image_urls": ["http://example.com/img.jpg"],
        "references": [
            {"chunk_id": "chunk-001", "title": "维修手册", "source": "知识库"},
        ],
        "is_stream": False,
    }
    
    node_save_qa(mock_state)
    print("QA保存完成")
