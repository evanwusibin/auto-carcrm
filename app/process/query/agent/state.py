from typing_extensions import TypedDict
from typing import List
import copy


class QueryGraphState(TypedDict):
    """
    QueryGraphState 定义了整个查询流程中流转的数据结构。
    TypedDict 让我们在代码中能有自动补全和类型检查。
    使用字典式访问（如 state["session_id"]、state.get("answer")）。
    """
    session_id: str
    original_query: str
    rewritten_query: str
    is_stream: bool

    intent: str
    extracted_entities: dict

    embedding_chunks: list
    hyde_embedding_chunks: list
    web_search_docs: list
    keyword_chunks: list
    structured_chunks: list
    case_chunks: list

    rrf_chunks: list
    filtered_chunks: list
    reranked_docs: list

    confidence_score: float
    need_followup: bool
    followup_question: str

    prompt: str
    answer: str
    image_urls: List[str]

    item_names: List[str]
    candidate_item_names: List[str]
    history: list


query_graph_default_state: QueryGraphState = {
    "session_id": "",
    "original_query": "",
    "rewritten_query": "",
    "is_stream": False,

    "intent": "",
    "extracted_entities": {},

    "embedding_chunks": [],
    "hyde_embedding_chunks": [],
    "web_search_docs": [],
    "keyword_chunks": [],
    "structured_chunks": [],
    "case_chunks": [],

    "rrf_chunks": [],
    "filtered_chunks": [],
    "reranked_docs": [],

    "confidence_score": 0.0,
    "need_followup": False,
    "followup_question": "",

    "prompt": "",
    "answer": "",
    "image_urls": [],

    "item_names": [],
    "candidate_item_names": [],
    "history": [],
}


def create_query_default_state(**overrides) -> QueryGraphState:
    state = copy.deepcopy(query_graph_default_state)
    state.update(overrides)
    return state


def get_query_default_state() -> QueryGraphState:
    return copy.deepcopy(query_graph_default_state)
