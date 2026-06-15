# -*- coding: utf-8 -*-
"""节点：知识文档持久化"""
import sys
from app.shared.runtime.logger import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.knowledge_persist_service import persist_knowledge


@node_log("node_save_knowledge")
def node_save_knowledge(state: ImportGraphState) -> ImportGraphState:
    add_running_task(state["task_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    state = persist_knowledge(state)
    add_done_task(state["task_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    return state
