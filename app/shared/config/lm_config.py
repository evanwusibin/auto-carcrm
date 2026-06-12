"""
LLM 配置模块，负责读取对话模型与视觉模型相关环境变量。
"""
from dataclasses import dataclass

from app.shared.config.common import env_bool, env_float, env_str


@dataclass
class LLMConfig:
    base_url: str
    api_key: str
    lv_model: str
    llm_model: str
    llm_temperature: float
    # 视觉功能总开关：false 时 vision_chat() 应跳过图片调用，业务侧需判空降级
    vl_enabled: bool = True


lm_config = LLMConfig(
    base_url=env_str("OPENAI_BASE_URL"),
    api_key=env_str("OPENAI_API_KEY"),
    lv_model=env_str("LLM_VL_MODEL") or env_str("VL_MODEL"),
    llm_model=env_str("LLM_DEFAULT_MODEL"),
    llm_temperature=env_float("LLM_DEFAULT_TEMPERATURE"),
    vl_enabled=env_bool("VL_ENABLED", default=True),
)


def is_vl_enabled() -> bool:
    """
    业务侧统一使用这个函数判断是否启用视觉功能。

    Returns:
        bool: True=可调用视觉模型；False=必须跳过图片请求并降级为纯文本。
    """
    return bool(lm_config.vl_enabled)
