"""
工具模块，负责提供 reranker 相关的辅助能力。
"""
from app.shared.config.reranker_config import reranker_config
from app.shared.runtime.logger import logger

_reranker_model = None
_reranker_failed = False


def get_reranker_model():
    """
    获取重排模型单例对象。
    如果模型加载失败（如内存不足），返回 None，调用方需做降级处理。
    """
    global _reranker_model, _reranker_failed
    if _reranker_failed:
        return None
    if _reranker_model is None:
        try:
            from FlagEmbedding import FlagReranker
            logger.info("开始初始化重排模型")
            _reranker_model = FlagReranker(
                model_name_or_path=reranker_config.bge_reranker_large,
                device=reranker_config.bge_reranker_device,
                use_fp16=reranker_config.bge_reranker_fp16,
            )
            logger.success("重排模型初始化成功")
        except Exception as e:
            logger.warning(f"重排模型加载失败，后续 rerank 节点将使用 RRF 分数降级: {e}")
            _reranker_failed = True
            return None
    return _reranker_model
