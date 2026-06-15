# -*- coding: utf-8 -*-
"""节点：QA会话/消息/引用落库"""
import sys
from app.shared.runtime.logger import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.answer_service import save_qa_records


@node_log("node_save_qa")
def node_save_qa(state: QueryGraphState) -> QueryGraphState:
    add_running_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    state = save_qa_records(state)
    add_done_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    return state
