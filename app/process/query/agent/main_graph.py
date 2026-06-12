from langgraph.graph import StateGraph, END
from app.process.query.agent.nodes.node_item_name_confirm import node_item_name_confirm
from app.process.query.agent.nodes.node_search_embedding import node_search_embedding
from app.process.query.agent.nodes.node_search_embedding_hyde import node_search_embedding_hyde
from app.process.query.agent.nodes.node_web_search_mcp import node_web_search_mcp
from app.process.query.agent.nodes.node_rerank import node_rerank
from app.process.query.agent.nodes.node_rrf import node_rrf
from app.process.query.agent.nodes.node_answer_output import node_answer_output
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger
from app.shared.config.rag_config import rag_config

# 1、定义主图对象
query_graph_builder = StateGraph(QueryGraphState)

# 2、添加节点
query_graph_builder.add_node("node_item_name_confirm", node_item_name_confirm)
query_graph_builder.add_node("node_search_embedding", node_search_embedding)

# 根据配置决定是否添加可选节点
if rag_config.enable_hyde:
    query_graph_builder.add_node("node_search_embedding_hyde", node_search_embedding_hyde)
    logger.info("✅ HyDE 检索已启用")

if rag_config.enable_web:
    query_graph_builder.add_node("node_web_search_mcp", node_web_search_mcp)
    logger.info("✅ Web 搜索已启用")

query_graph_builder.add_node("node_rrf", node_rrf)
query_graph_builder.add_node("node_rerank", node_rerank)
query_graph_builder.add_node("node_answer_output", node_answer_output)

# 3、设置入口节点
query_graph_builder.set_entry_point("node_item_name_confirm")

# 3.1 定义条件的路由函数
def node_item_name_confirm_after(state: QueryGraphState):
    if state.get('answer'):
        # 有值：没有识别到 item_name，提前结束
        logger.info(f"本次没有明确的item_name,提前结束，待用户确定！{state.get('answer')}")
        return "node_answer_output"
    else:
        # 没有：有明确的 item_name，继续检索
        logger.info(f"有明确的item_name:{state.get('item_names')} 业务继续继续即可！！")
        # 构建并发节点列表（必选 + 可选）
        parallel_nodes = [
            "node_search_embedding",
        ]
        if rag_config.enable_hyde:
            parallel_nodes.append("node_search_embedding_hyde")
        if rag_config.enable_web:
            parallel_nodes.append("node_web_search_mcp")
        return tuple(parallel_nodes)

# 3.2 设置条件边
query_graph_builder.add_conditional_edges(
    "node_item_name_confirm",
    node_item_name_confirm_after,
    {
        "node_answer_output": "node_answer_output",
        "node_search_embedding": "node_search_embedding",
        "node_search_embedding_hyde": "node_search_embedding_hyde",
        "node_web_search_mcp": "node_web_search_mcp",
    }
)

# 4、添加边（所有检索节点 → rrf）
query_graph_builder.add_edge("node_search_embedding", "node_rrf")
if rag_config.enable_hyde:
    query_graph_builder.add_edge("node_search_embedding_hyde", "node_rrf")
if rag_config.enable_web:
    query_graph_builder.add_edge("node_web_search_mcp", "node_rrf")

query_graph_builder.add_edge("node_rrf", "node_rerank")
query_graph_builder.add_edge("node_rerank", "node_answer_output")
query_graph_builder.add_edge("node_answer_output", END)

# 5、编译图
query_graph_app = query_graph_builder.compile()

logger.info(f"查询图编译完成，HyDE={rag_config.enable_hyde}, Web={rag_config.enable_web}")
