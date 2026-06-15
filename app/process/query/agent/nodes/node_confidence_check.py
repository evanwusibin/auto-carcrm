# -*- coding: utf-8 -*-
"""节点：置信度判断"""
import sys
from app.shared.runtime.logger import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.confidence_service import check_confidence


@node_log("node_confidence_check")
def node_confidence_check(state: QueryGraphState) -> QueryGraphState:
    add_running_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    state = check_confidence(state)
    add_done_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    return {"confidence": state.get("confidence"), "needs_clarify": state.get("needs_clarify")}
