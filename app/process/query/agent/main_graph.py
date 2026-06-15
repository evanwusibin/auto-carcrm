# -*- coding: utf-8 -*-
"""
查询流程主图
作用：串联所有查询节点，定义执行顺序和条件边
参考老师 main_graph.py 的代码风格
"""
from langgraph.graph import StateGraph, END
from app.shared.runtime.logger import logger
from app.shared.config.rag_config import rag_config

# 导入所有节点
from app.process.query.agent.nodes.node_item_name_confirm import node_item_name_confirm
from app.process.query.agent.nodes.node_intent_recognition import node_intent_recognition
from app.process.query.agent.nodes.node_entity_extraction import node_entity_extraction
from app.process.query.agent.nodes.node_search_embedding import node_search_embedding
from app.process.query.agent.nodes.node_keyword_search import node_keyword_search
from app.process.query.agent.nodes.node_structured_query import node_structured_query
from app.process.query.agent.nodes.node_case_search import node_case_search
from app.process.query.agent.nodes.node_rrf import node_rrf
from app.process.query.agent.nodes.node_metadata_filter import node_metadata_filter
from app.process.query.agent.nodes.node_rerank import node_rerank
from app.process.query.agent.nodes.node_confidence_check import node_confidence_check
from app.process.query.agent.nodes.node_answer_output import node_answer_output
from app.process.query.agent.nodes.node_save_qa import node_save_qa

# 导入可选节点
from app.process.query.agent.nodes.node_search_embedding_hyde import node_search_embedding_hyde
from app.process.query.agent.nodes.node_web_search_mcp import node_web_search_mcp

# 导入 state
from app.process.query.agent.state import QueryGraphState


query_graph_builder = StateGraph(QueryGraphState)

query_graph_builder.add_node("node_item_name_confirm", node_item_name_confirm)
query_graph_builder.add_node("node_intent_recognition", node_intent_recognition)
query_graph_builder.add_node("node_entity_extraction", node_entity_extraction)
query_graph_builder.add_node("node_search_embedding", node_search_embedding)
query_graph_builder.add_node("node_keyword_search", node_keyword_search)
query_graph_builder.add_node("node_structured_query", node_structured_query)
query_graph_builder.add_node("node_case_search", node_case_search)
query_graph_builder.add_node("node_rrf", node_rrf)
query_graph_builder.add_node("node_metadata_filter", node_metadata_filter)
query_graph_builder.add_node("node_rerank", node_rerank)
query_graph_builder.add_node("node_confidence_check", node_confidence_check)
query_graph_builder.add_node("node_answer_output", node_answer_output)
query_graph_builder.add_node("node_save_qa", node_save_qa)

query_graph_builder.add_node("node_search_embedding_hyde", node_search_embedding_hyde)
query_graph_builder.add_node("node_web_search_mcp", node_web_search_mcp)
logger.info("✅ HyDE 检索节点已添加")
logger.info("✅ Web 搜索节点已添加")
logger.info("✅ Metadata Filter 节点已添加")

query_graph_builder.set_entry_point("node_item_name_confirm")


def node_item_name_confirm_after(state: QueryGraphState):
    if state.get('answer'):
        logger.info(f"本次没有明确的item_name,提前结束，待用户确定！{state.get('answer')}")
        return "node_answer_output"
    else:
        logger.info(f"有明确的item_name:{state.get('item_names')} 业务继续继续即可！！")
        return "node_intent_recognition"


query_graph_builder.add_conditional_edges(
    "node_item_name_confirm",
    node_item_name_confirm_after,
    {
        "node_answer_output": "node_answer_output",
        "node_intent_recognition": "node_intent_recognition",
    }
)

# 意图识别后的条件边：闲聊/投诉直接跳到答案生成，不走检索
def node_intent_recognition_after(state: QueryGraphState):
    intent = state.get('intent', '')
    logger.info(f"[意图路由] 意图={intent}")
    
    # 闲聊和投诉直接生成答案，不走检索流程
    if intent in ['chitchat', 'complaint']:
        logger.info(f"[意图路由] 意图={intent}，跳过检索，直接生成答案")
        # 标记为跳过检索
        state['skip_retrieval'] = True
        state['embedding_chunks'] = []
        state['hyde_embedding_chunks'] = []
        state['keyword_chunks'] = []
        state['structured_chunks'] = []
        state['case_chunks'] = []
        state['rrf_chunks'] = []
        state['reranked_docs'] = []
        return "node_answer_output"
    else:
        logger.info(f"[意图路由] 意图={intent}，走完整检索流程")
        return "node_entity_extraction"


query_graph_builder.add_conditional_edges(
    "node_intent_recognition",
    node_intent_recognition_after,
    {
        "node_answer_output": "node_answer_output",
        "node_entity_extraction": "node_entity_extraction",
    }
)

query_graph_builder.add_edge("node_entity_extraction", "node_search_embedding")
query_graph_builder.add_edge("node_entity_extraction", "node_keyword_search")
query_graph_builder.add_edge("node_entity_extraction", "node_structured_query")
query_graph_builder.add_edge("node_entity_extraction", "node_case_search")
query_graph_builder.add_edge("node_entity_extraction", "node_search_embedding_hyde")
query_graph_builder.add_edge("node_entity_extraction", "node_web_search_mcp")

query_graph_builder.add_edge("node_search_embedding", "node_rrf")
query_graph_builder.add_edge("node_keyword_search", "node_rrf")
query_graph_builder.add_edge("node_structured_query", "node_rrf")
query_graph_builder.add_edge("node_case_search", "node_rrf")
query_graph_builder.add_edge("node_search_embedding_hyde", "node_rrf")
query_graph_builder.add_edge("node_web_search_mcp", "node_rrf")

query_graph_builder.add_edge("node_rrf", "node_metadata_filter")
query_graph_builder.add_edge("node_metadata_filter", "node_rerank")
query_graph_builder.add_edge("node_rerank", "node_confidence_check")


def node_confidence_check_after(state: QueryGraphState):
    if state.get('need_followup'):
        logger.info(f"置信度不足，需要追问：{state.get('followup_question')}")
        state["answer"] = state.get("followup_question", "抱歉，我没有找到足够的信息来回答您的问题。")
        return "node_answer_output"
    else:
        logger.info("置信度足够，继续生成答案")
        return "node_answer_output"


query_graph_builder.add_conditional_edges(
    "node_confidence_check",
    node_confidence_check_after,
    {
        "node_answer_output": "node_answer_output",
    }
)

query_graph_builder.add_edge("node_answer_output", "node_save_qa")
query_graph_builder.add_edge("node_save_qa", END)

query_graph_app = query_graph_builder.compile()

logger.info("查询图编译完成，HyDE=True, Web=True, MetadataFilter=True")
