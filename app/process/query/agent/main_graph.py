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
from app.process.query.agent.nodes.node_rerank import node_rerank
from app.process.query.agent.nodes.node_confidence_check import node_confidence_check
from app.process.query.agent.nodes.node_answer_output import node_answer_output
from app.process.query.agent.nodes.node_save_qa import node_save_qa

# 导入可选节点
from app.process.query.agent.nodes.node_search_embedding_hyde import node_search_embedding_hyde
from app.process.query.agent.nodes.node_web_search_mcp import node_web_search_mcp

# 导入 state
from app.process.query.agent.state import QueryGraphState


# 1. 定义主图对象
query_graph_builder = StateGraph(QueryGraphState)

# 2. 添加节点
query_graph_builder.add_node("node_item_name_confirm", node_item_name_confirm)
query_graph_builder.add_node("node_intent_recognition", node_intent_recognition)
query_graph_builder.add_node("node_entity_extraction", node_entity_extraction)
query_graph_builder.add_node("node_search_embedding", node_search_embedding)
query_graph_builder.add_node("node_keyword_search", node_keyword_search)
query_graph_builder.add_node("node_structured_query", node_structured_query)
query_graph_builder.add_node("node_case_search", node_case_search)
query_graph_builder.add_node("node_rrf", node_rrf)
query_graph_builder.add_node("node_rerank", node_rerank)
query_graph_builder.add_node("node_confidence_check", node_confidence_check)
query_graph_builder.add_node("node_answer_output", node_answer_output)
query_graph_builder.add_node("node_save_qa", node_save_qa)

# 根据配置决定是否添加可选节点
if rag_config.enable_hyde:
    query_graph_builder.add_node("node_search_embedding_hyde", node_search_embedding_hyde)
    logger.info("✅ HyDE 检索已启用")

if rag_config.enable_web:
    query_graph_builder.add_node("node_web_search_mcp", node_web_search_mcp)
    logger.info("✅ Web 搜索已启用")


# 3. 设置入口节点
query_graph_builder.set_entry_point("node_item_name_confirm")


# 3.1 定义条件的路由函数（node_item_name_confirm 之后）
def node_item_name_confirm_after(state: QueryGraphState):
    """
    node_item_name_confirm 之后的路由逻辑
    
    判断：
    - 如果有 answer（没有识别到 item_name），提前结束
    - 如果没有 answer（有明确的 item_name），继续检索
    """
    if state.get('answer'):
        # 有值：没有识别到 item_name，提前结束
        logger.info(f"本次没有明确的item_name,提前结束，待用户确定！{state.get('answer')}")
        return "node_answer_output"
    else:
        # 没有：有明确的 item_name，继续检索
        logger.info(f"有明确的item_name:{state.get('item_names')} 业务继续继续即可！！")
        return "node_intent_recognition"


# 3.2 设置条件边（node_item_name_confirm 之后）
query_graph_builder.add_conditional_edges(
    "node_item_name_confirm",
    node_item_name_confirm_after,
    {
        "node_answer_output": "node_answer_output",
        "node_intent_recognition": "node_intent_recognition",
    }
)


# 4. 添加静态边（节点之间的连接）
# node_intent_recognition → node_entity_extraction
query_graph_builder.add_edge("node_intent_recognition", "node_entity_extraction")

# node_entity_extraction → 四路并行检索
# 这里使用条件边，根据配置决定并行哪些节点
def node_entity_extraction_after(state: QueryGraphState):
    """
    node_entity_extraction 之后的路由逻辑
    
    返回并行执行的节点列表
    """
    parallel_nodes = [
        "node_search_embedding",
        "node_keyword_search",
        "node_structured_query",
        "node_case_search",
    ]
    
    if rag_config.enable_hyde:
        parallel_nodes.append("node_search_embedding_hyde")
    if rag_config.enable_web:
        parallel_nodes.append("node_web_search_mcp")
    
    return tuple(parallel_nodes)


query_graph_builder.add_conditional_edges(
    "node_entity_extraction",
    node_entity_extraction_after,
    {
        "node_search_embedding": "node_search_embedding",
        "node_keyword_search": "node_keyword_search",
        "node_structured_query": "node_structured_query",
        "node_case_search": "node_case_search",
        "node_search_embedding_hyde": "node_search_embedding_hyde",
        "node_web_search_mcp": "node_web_search_mcp",
    }
)


# 5. 所有检索节点 → node_rrf
query_graph_builder.add_edge("node_search_embedding", "node_rrf")
query_graph_builder.add_edge("node_keyword_search", "node_rrf")
query_graph_builder.add_edge("node_structured_query", "node_rrf")
query_graph_builder.add_edge("node_case_search", "node_rrf")

if rag_config.enable_hyde:
    query_graph_builder.add_edge("node_search_embedding_hyde", "node_rrf")
if rag_config.enable_web:
    query_graph_builder.add_edge("node_web_search_mcp", "node_rrf")


# 6. node_rrf → node_rerank → node_confidence_check
query_graph_builder.add_edge("node_rrf", "node_rerank")
query_graph_builder.add_edge("node_rerank", "node_confidence_check")


# 7. node_confidence_check 之后的条件边
def node_confidence_check_after(state: QueryGraphState):
    """
    node_confidence_check 之后的路由逻辑
    
    判断：
    - 如果置信度足够（不需要追问），生成答案
    - 如果置信度不足（需要追问），直接返回追问问题
    """
    if state.get('need_followup'):
        # 需要追问
        logger.info(f"置信度不足，需要追问：{state.get('followup_question')}")
        # 将追问问题设为 answer，直接返回
        state["answer"] = state.get("followup_question", "抱歉，我没有找到足够的信息来回答您的问题。")
        return "node_answer_output"
    else:
        # 置信度足够，生成答案
        logger.info(f"置信度足够，继续生成答案")
        return "node_answer_output"


query_graph_builder.add_conditional_edges(
    "node_confidence_check",
    node_confidence_check_after,
    {
        "node_answer_output": "node_answer_output",
    }
)


# 8. node_answer_output → node_save_qa → END
query_graph_builder.add_edge("node_answer_output", "node_save_qa")
query_graph_builder.add_edge("node_save_qa", END)


# 9. 编译图
query_graph_app = query_graph_builder.compile()

logger.info(f"查询图编译完成，HyDE={rag_config.enable_hyde}, Web={rag_config.enable_web}")
