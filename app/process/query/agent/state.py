from typing_extensions import TypedDict
from typing import List
import copy


class QueryGraphState(TypedDict):
    """
    QueryGraphState 定义了整个查询流程中流转的数据结构。
    TypedDict 让我们在代码中能有自动补全和类型检查。
    使用字典式访问（如 state["session_id"]、state.get("answer")）。
    """
    # ==================== 基础信息 ====================
    session_id: str  # 会话唯一标识
    original_query: str  # 用户原始问题
    rewritten_query: str  # 改写后的问题
    is_stream: bool  # 是否流式输出标记

    # ==================== 意图识别 ====================
    intent: str  # 意图类型（pre_sales_consultation/after_sales_service/...）
    extracted_entities: dict  # 抽取的实体（vehicle_model/vin/fault_codes/...）

    # ==================== 检索结果 ====================
    embedding_chunks: list  # 普通向量检索回来的切片
    hyde_embedding_chunks: list  # HyDE 检索回来的切片
    web_search_docs: list  # 网络搜索回来的文档
    keyword_chunks: list  # 关键词检索回来的切片
    structured_chunks: list  # 结构化查询回来的切片
    case_chunks: list  # 案例检索回来的切片

    # ==================== 融合排序 ====================
    rrf_chunks: list  # RRF 融合排序后的切片
    reranked_docs: list  # 重排序后的最终 Top-K 文档

    # ==================== 置信度检查 ====================
    confidence_score: float  # 置信度分数（0-1）
    need_followup: bool  # 是否需要追问
    followup_question: str  # 追问问题

    # ==================== 生成结果 ====================
    prompt: str  # 组装好的 Prompt
    answer: str  # 最终生成的答案
    image_urls: List[str]  # 答案中引用的图片链接

    # ==================== 辅助信息 ====================
    item_names: List[str]  # 提取出的商品名称
    history: list  # 历史对话记录


# ========================
# 默认状态（全部为空）
# ========================
query_graph_default_state: QueryGraphState = {
    # 基础信息
    "session_id": "",
    "original_query": "",
    "rewritten_query": "",
    "is_stream": False,

    # 意图识别
    "intent": "",
    "extracted_entities": {},

    # 检索结果
    "embedding_chunks": [],
    "hyde_embedding_chunks": [],
    "web_search_docs": [],
    "keyword_chunks": [],
    "structured_chunks": [],
    "case_chunks": [],

    # 融合排序
    "rrf_chunks": [],
    "reranked_docs": [],

    # 置信度检查
    "confidence_score": 0.0,
    "need_followup": False,
    "followup_question": "",

    # 生成结果
    "prompt": "",
    "answer": "",
    "image_urls": [],

    # 辅助信息
    "item_names": [],
    "history": [],
}


# ========================
# 创建默认状态（可覆盖）
# ========================
def create_query_default_state(**overrides) -> QueryGraphState:
    """
    创建查询流程的默认状态，支持覆盖字段
    """
    state = copy.deepcopy(query_graph_default_state)
    state.update(overrides)
    return state


# ========================
# 获取干净状态
# ========================
def get_query_default_state() -> QueryGraphState:
    """
    返回一个新的状态实例，避免全局变量污染。
    """
    return copy.deepcopy(query_graph_default_state)
