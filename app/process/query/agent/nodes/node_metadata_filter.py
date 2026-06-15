# -*- coding: utf-8 -*-
"""节点：元数据过滤（车型/版本/有效期/权限）"""
import sys
from app.shared.runtime.logger import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.metadata_filter_service import filter_by_metadata


@node_log("node_metadata_filter")
def node_metadata_filter(state: QueryGraphState) -> QueryGraphState:
    add_running_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    state = filter_by_metadata(state)
    add_done_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    return {"filtered_chunks": state.get("filtered_chunks")}
