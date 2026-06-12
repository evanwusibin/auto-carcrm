"""RAG 配置。"""
from dataclasses import dataclass

from app.shared.config.common import env_float, env_int, env_bool


@dataclass
class RagConfig:
    vector_topk: int
    keyword_topk: int
    case_topk: int
    final_topk: int
    confidence_threshold: float
    rrf_k: int
    max_context_chars: int
    enable_hyde: bool
    enable_web: bool


rag_config = RagConfig(
    vector_topk=env_int('RAG_VECTOR_TOPK', 20),
    keyword_topk=env_int('RAG_KEYWORD_TOPK', 10),
    case_topk=env_int('RAG_CASE_TOPK', 5),
    final_topk=env_int('RAG_FINAL_TOPK', 5),
    confidence_threshold=env_float('RAG_CONFIDENCE_THRESHOLD', 0.55),
    rrf_k=env_int('RAG_RRF_K', 60),
    max_context_chars=env_int('RAG_MAX_CONTEXT_CHARS', 10000),
    enable_hyde=env_bool('RAG_ENABLE_HYDE', False),
    enable_web=env_bool('RAG_ENABLE_WEB', False),
)
