# -*- coding: utf-8 -*-
"""节点：实体抽取（车型/VIN/故障码/里程/部件）"""
import sys
from app.shared.runtime.logger import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.entity_extraction_service import extract_entities


@node_log("node_entity_extraction")
def node_entity_extraction(state: QueryGraphState) -> QueryGraphState:
    add_running_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    state = extract_entities(state)
    add_done_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    return {"entities": state.get("entities")}
