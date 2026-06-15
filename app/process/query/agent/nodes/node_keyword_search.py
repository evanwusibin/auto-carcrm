# -*- coding: utf-8 -*-
"""节点：BM25关键词检索"""
import sys
from app.shared.runtime.logger import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.keyword_search_service import search_by_keywords


@node_log("node_keyword_search")
def node_keyword_search(state: QueryGraphState) -> QueryGraphState:
    add_running_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    state = search_by_keywords(state)
    add_done_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    return {"keyword_chunks": state.get("keyword_chunks", [])}
