# -*- coding: utf-8 -*-
"""
QA持久化服务
作用：保存问答会话、消息和引用到 MongoDB
参考老师 answer_service.py 的代码风格
"""
from datetime import datetime

from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState
from app.infra.persistence.history_repository import history_repository


@step_log("validate_qa_state")
def validate_qa_state(state: QueryGraphState):
    """校验QA保存所需参数"""
    session_id = state.get("session_id")
    if not session_id:
        logger.error("session_id 为空，无法保存QA")
        raise ValueError("session_id 为空，无法保存QA")
    
    original_query = state.get("original_query")
    if not original_query:
        logger.error("original_query 为空，无法保存QA")
        raise ValueError("original_query 为空，无法保存QA")
    
    answer = state.get("answer")
    if not answer:
        logger.error("answer 为空，无法保存QA")
        raise ValueError("answer 为空，无法保存QA")
    
    return session_id, original_query, answer


def save_qa_session(state: QueryGraphState):
    """
    QA保存主函数（参考老师 answer_service.py 风格）
    
    输入：state（包含 session_id, original_query, answer, image_urls, references）
    输出：无（写入 MongoDB）
    """
    # 1. 校验参数
    session_id, original_query, answer = validate_qa_state(state)
    
    # 2. 保存用户消息
    history_repository.save_message(
        session_id=session_id,
        role="user",
        text=original_query,
        item_names=state.get("item_names", []),
        rewritten_query=state.get("rewritten_query", original_query),
    )
    logger.info(f"保存用户消息：session_id={session_id}")
    
    # 3. 保存助手回答
    history_repository.save_message(
        session_id=session_id,
        role="assistant",
        text=answer,
        item_names=state.get("item_names", []),
        image_urls=state.get("image_urls", []),
    )
    logger.info(f"保存助手回答：session_id={session_id}")
    
    # 4. 保存引用来源（如果有）
    references = state.get("references", [])
    if references:
        logger.info(f"保存引用来源：session_id={session_id}, references={len(references)} 条")
    
    logger.info(f"QA保存完成：session_id={session_id}")
