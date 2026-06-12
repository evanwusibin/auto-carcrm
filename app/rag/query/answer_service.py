# -*- coding: utf-8 -*-
"""
答案生成服务
作用：调用 LLM 生成最终答案
参考老师 answer_service.py 的代码风格
"""
import re
from app.infra.llm.providers import llm_provider
from app.infra.persistence.history_repository import history_repository
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.load_prompt import load_prompt
from app.shared.utils.task_utils import add_done_task, add_running_task, push_to_session
from app.shared.utils.sse_utils import SSEEvent
from app.shared.runtime.logger import logger, step_log
from app.rag.query.prompt_builder import build_prompt


@step_log("validate_answer_state")
def validate_answer_state(state: QueryGraphState):
    """校验答案生成所需参数"""
    reranked_docs = state.get("reranked_docs", [])
    item_names = state.get("item_names", [])
    rewritten_query = state.get("rewritten_query", "")
    
    if not rewritten_query:
        logger.error("rewritten_query 为空，无法生成答案")
        raise ValueError("rewritten_query 为空，无法生成答案")
    
    return reranked_docs, item_names, rewritten_query


def check_state_had_answer(state):
    """
    检查 state 是否已有 answer（追问或拒绝回答）
    
    输入：state
    输出：True/False
    """
    answer = state.get("answer")
    if not answer:
        logger.info("没有 answer，继续生成答案")
        return False
    
    # 已有 answer，流式返回
    is_stream = state.get("is_stream", False)
    if is_stream:
        for ch in answer:
            push_to_session(
                state.get("session_id"),
                SSEEvent.DELTA,
                data={"delta": ch}
            )
    
    return True


def call_llm_generate(prompt_text, state):
    """
    调用 LLM 生成答案（支持流式/非流式）
    
    输入：prompt_text（提示词），state
    输出：无（直接修改 state['answer']）
    """
    final_answer = ""
    
    # 1. 获取模型对象
    llm_client = llm_provider.chat()
    
    # 2. 判断是否流式调用
    is_stream = state.get("is_stream", False)
    
    if is_stream:
        # 流式返回
        stream = llm_client.stream(prompt_text)
        for chunk in stream:
            current_content = chunk.content
            push_to_session(
                state.get("session_id"),
                SSEEvent.DELTA,
                data={"delta": current_content}
            )
            final_answer += current_content
    else:
        # 非流式返回
        response = llm_client.invoke(prompt_text)
        final_answer = response.content
    
    # 3. 写入 state
    state["answer"] = final_answer


def extract_image_urls(reranked_docs, state):
    """
    从引用文档中提取图片 URL
    
    输入：reranked_docs（重排序后的文档列表），state
    输出：无（直接修改 state['image_urls']）
    """
    image_urls = []
    
    # 匹配 markdown 图片正则
    reg = re.compile(r"\!\[.*?\]\((.*?)\)")
    
    for doc in reranked_docs:
        url = doc.get("url", "")
        text = doc.get("text", "")
        
        # 提取 url
        if url and url.endswith((".jpg", ".jpeg", ".png", ".gif", "svg")):
            image_urls.append(url)
        
        # 提取 text 中的图片
        for image_url in reg.findall(text):
            if image_url not in image_urls:
                image_urls.append(image_url)
    
    # 写入 state
    state["image_urls"] = image_urls


def save_history_message(state):
    """
    保存历史对话记录
    
    输入：state
    输出：无（写入 MongoDB）
    """
    history_repository.save_message(
        session_id=state["session_id"],
        role="assistant",
        text=state.get("answer"),
        rewritten_query=state.get("rewritten_query"),
        item_names=state.get("item_names", []),
        image_urls=state.get("image_urls", [])
    )


def generate_answer(state: QueryGraphState) -> QueryGraphState:
    """
    答案生成主函数（参考老师 answer_service.py 风格）
    
    输入：state（包含 reranked_docs, item_names, rewritten_query, session_id）
    输出：state（新增 answer, image_urls）
    """
    # 1. 检查是否已有 answer（追问或拒绝回答）
    has_answer = check_state_had_answer(state)
    
    # 2. 如果没有 answer，才调用模型生成
    if not has_answer:
        # 3. 校验参数
        reranked_docs, item_names, rewritten_query = validate_answer_state(state)
        
        # 4. 构建提示词（使用 prompt_builder）
        prompt_text = build_prompt(state)
        
        # 5. 调用 LLM 生成答案
        call_llm_generate(prompt_text, state)
        
        # 6. 提取图片 URL
        extract_image_urls(reranked_docs, state)
    
    # 7. 保存历史记录
    save_history_message(state)
    
    # 8. 返回 state
    return state
