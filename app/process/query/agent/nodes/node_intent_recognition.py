# -*- coding: utf-8 -*-
"""节点：意图识别（售前/售后/用车/投诉/闲聊/办理）"""
import sys
from app.shared.runtime.logger import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.query.agent.state import QueryGraphState
from app.rag.query.intent_recognition_service import recognize_intent


@node_log("node_intent_recognition")
def node_intent_recognition(state: QueryGraphState) -> QueryGraphState:
    add_running_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    state = recognize_intent(state)
    add_done_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    return {"intent": state.get("intent")}
