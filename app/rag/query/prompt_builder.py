# -*- coding: utf-8 -*-
"""
提示词构建服务
作用：组装 answer_out.prompt 的 context/history/item_names/question 四段
参考老师 answer_service.py 的代码风格
"""
from app.infra.llm.providers import llm_provider
from app.infra.persistence.history_repository import history_repository
from app.shared.runtime.load_prompt import load_prompt
from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState


@step_log("validate_prompt_state")
def validate_prompt_state(state: QueryGraphState):
    """校验提示词构建所需参数"""
    reranked_docs = state.get("reranked_docs", [])
    item_names = state.get("item_names", [])
    rewritten_query = state.get("rewritten_query", "")
    
    if not rewritten_query:
        logger.error("rewritten_query 为空，无法构建提示词")
        raise ValueError("rewritten_query 为空，无法构建提示词")
    
    return reranked_docs, item_names, rewritten_query


def build_context(reranked_docs: list[dict]) -> str:
    """
    构建上下文（reranked_docs 格式化为字符串）
    
    输入：reranked_docs（重排序后的文档列表）
    输出：context（格式化后的上下文字符串）
    """
    context = ""
    for i, doc in enumerate(reranked_docs, 1):
        title = doc.get("title", "未知标题")
        source = "网络搜索" if doc.get("type") == "web" else "向量库"
        score = doc.get("score", 0.0)
        text = doc.get("text", "")
        
        context += f"[{i}] 标题：{title} 来源：{source} 评分：{score:.2f}\n内容：{text}\n\n"
    
    return context


def build_history(session_id: str) -> str:
    """
    构建历史对话记录
    
    输入：session_id（会话ID）
    输出：history（格式化后的历史记录字符串）
    """
    # 从 MongoDB 获取历史记录
    history = history_repository.list_recent(session_id, limit=10)
    
    if not history:
        return "没有对话记录!"
    
    # 过滤出有 item_names 的记录
    final_message_list = [
        item for item in history 
        if item.get("item_names") and len(item.get("item_names")) > 0
    ]
    
    if not final_message_list:
        return "没有对话记录!"
    
    # 格式化历史记录
    history_text = ""
    for index, item in enumerate(final_message_list, start=1):
        role = "提问" if item.get("role") == "user" else "回答"
        content = item.get("rewritten_query") if item.get("role") == "user" else item.get("text", "")
        item_names = ",".join(item.get("item_names", []))
        
        history_text += f"序号：{index}，角色：{role}，内容：{content}，关联主体：{item_names}\n"
    
    return history_text


def build_item_names(item_names: list[str]) -> str:
    """
    构建商品名称字符串
    
    输入：item_names（商品名称列表）
    输出：item_names_text（格式化后的商品名称字符串）
    """
    return "、".join(item_names) if item_names else "无"


def build_prompt(state: QueryGraphState) -> str:
    """
    提示词构建主函数（参考老师 answer_service.py 风格）
    
    输入：state（包含 reranked_docs, item_names, rewritten_query, session_id）
    输出：prompt_text（构建好的提示词）
    """
    # 1. 校验参数
    reranked_docs, item_names, rewritten_query = validate_prompt_state(state)
    
    # 2. 构建上下文
    context = build_context(reranked_docs)
    
    # 3. 构建历史记录
    session_id = state.get("session_id", "")
    history = build_history(session_id)
    
    # 4. 构建商品名称
    item_names_text = build_item_names(item_names)
    
    # 5. 加载提示词模板
    prompt_text = load_prompt(
        "answer_out",
        context=context,
        history=history,
        item_names=item_names_text,
        question=rewritten_query,
    )
    
    logger.info(f"提示词构建完成：{rewritten_query[:50]}...")
    
    return prompt_text
