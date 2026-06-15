# -*- coding: utf-8 -*-
"""节点：结构化查询（车辆档案/保养记录/质保规则）"""
import sys
from app.shared.runtime.logger import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.structured_query_service import query_structured_data


@node_log("node_structured_query")
def node_structured_query(state: QueryGraphState) -> QueryGraphState:
    add_running_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    state = query_structured_data(state)
    add_done_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    return {"structured_chunks": state.get("structured_chunks", [])}
