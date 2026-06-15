# -*- coding: utf-8 -*-
"""节点：元数据抽取（车型/版本/有效期）"""
import sys
from app.shared.runtime.logger import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.doc_meta_service import extract_doc_meta


@node_log("node_doc_meta")
def node_doc_meta(state: ImportGraphState) -> ImportGraphState:
    add_running_task(state["task_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    state = extract_doc_meta(state)
    add_done_task(state["task_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    return state
