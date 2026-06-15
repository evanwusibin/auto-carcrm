# -*- coding: utf-8 -*-
"""提示词构建服务"""
from app.shared.runtime.logger import logger, step_log
from app.shared.runtime.load_prompt import load_prompt


CONTEXT_MAX_CHARS = 6000


@step_log("build_prompt")
def build_prompt(state: dict) -> str:
    """
    从 state 中提取 reranked_docs / history / item_names / rewritten_query，
    组装成最终喂给 LLM 的 prompt。
    """
    logger.info("[prompt_builder] 构建提示词开始")

    rewritten_query = state.get("rewritten_query", "")
    item_names = state.get("item_names", [])
    history = state.get("history", [])
    intent = state.get("intent", "")
    reranked_docs = state.get("reranked_docs", [])

    context = build_context(reranked_docs)
    history_text = build_history_text(history)
    item_names_text = "、".join(item_names) if item_names else "未知"

    prompt = load_prompt(
        "answer_out",
        context=context,
        history=history_text,
        item_names=item_names_text,
        question=rewritten_query,
    )

    logger.info(f"[prompt_builder] 构建提示词完成，上下文长度={len(context)}，意图={intent}")
    return prompt


def build_context(reranked_docs: list) -> str:
    """将 reranked_docs 拼成参考内容字符串"""
    if not reranked_docs:
        return "暂无相关参考内容。"

    parts = []
    total_chars = 0
    for i, doc in enumerate(reranked_docs, start=1):
        title = doc.get("title", "")
        content = doc.get("text") or doc.get("content") or ""
        source_type = doc.get("type", "")
        source_tag = f"[来源: {source_type}]" if source_type else ""
        part = f"【片段{i}】{source_tag} {title}\n{content}".strip()
        if total_chars + len(part) > CONTEXT_MAX_CHARS:
            break
        parts.append(part)
        total_chars += len(part)

    return "\n\n".join(parts) if parts else "暂无相关参考内容。"


def build_history_text(history: list) -> str:
    """将历史对话列表转成文本"""
    if not history:
        return "无历史对话"

    lines = []
    for msg in history[-6:]:
        role = msg.get("role", "")
        text = msg.get("text") or msg.get("content") or ""
        label = "用户" if role == "user" else "助手"
        lines.append(f"{label}: {text}")
    return "\n".join(lines) if lines else "无历史对话"
