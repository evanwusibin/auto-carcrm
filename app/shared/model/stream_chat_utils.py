# -*- coding: utf-8 -*-
from typing import AsyncIterator
from langchain_core.messages import HumanMessage
from app.infra.llm.providers import llm_provider
from app.shared.runtime.logger import logger


async def stream_chat_response(messages: list) -> AsyncIterator[str]:
    """调用 LLM 流式输出，逐 token 返回。"""
    try:
        llm = llm_provider.chat()
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
    except Exception as exc:
        logger.error(f"[stream_chat_utils] 流式调用失败: {exc}")
        yield f"\n[错误] 流式调用失败: {exc}"


async def stream_chat_with_context(
    context: str,
    question: str,
    history: list | None = None,
) -> AsyncIterator[str]:
    """带上下文的流式问答。"""
    from app.shared.runtime.load_prompt import load_prompt

    prompt_text = load_prompt(
        "answer_out",
        context=context,
        item_names="",
        history=history or [],
        question=question,
    )
    messages = [HumanMessage(content=prompt_text)]
    async for token in stream_chat_response(messages):
        yield token
