# -*- coding: utf-8 -*-
"""
关键词检索服务
作用：使用 BM25 算法进行关键词精确检索
"""
from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState


@step_log("validate_keyword_state")
def validate_keyword_state(state: QueryGraphState):
    """校验关键词检索所需参数"""
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        raise ValueError("rewritten_query 为空，无法进行关键词检索")
    return rewritten_query


def tokenize_chinese(text: str) -> list[str]:
    """
    中文分词
    
    使用 jieba 进行中文分词，如果没有安装则使用简单分割
    """
    try:
        import jieba
        return list(jieba.cut(text))
    except ImportError:
        # 如果没有安装 jieba，使用简单分割
        logger.warning("jieba 未安装，使用简单分割")
        # 简单按字符分割（中文）和空格分割（英文）
        tokens = []
        for char in text:
            if char.isalnum():
                tokens.append(char)
            elif char == ' ':
                continue
            else:
                tokens.append(char)
        return tokens


def extract_keywords_from_entities(entities: dict) -> list[str]:
    """
    从实体中提取关键词
    
    输入：entities（实体字典）
    输出：keywords（关键词列表）
    """
    keywords = []
    
    # 故障码
    if entities.get("fault_codes"):
        keywords.append(entities["fault_codes"])
    
    # 车型
    if entities.get("vehicle_model"):
        keywords.append(entities["vehicle_model"])
    
    # 部件
    if entities.get("component"):
        keywords.append(entities["component"])
    
    return keywords


def search_by_keywords(state: QueryGraphState) -> QueryGraphState:
    """
    关键词检索主函数
    
    输入：state（包含 rewritten_query, extracted_entities）
    输出：state（新增 keyword_chunks 字段）
    """
    # 1. 校验参数
    rewritten_query = validate_keyword_state(state)
    
    # 2. 提取关键词
    entities = state.get("extracted_entities", {})
    entity_keywords = extract_keywords_from_entities(entities)
    
    # 3. 分词
    query_tokens = tokenize_chinese(rewritten_query)
    
    # 4. 合并关键词
    all_keywords = entity_keywords + query_tokens
    
    # 5. TODO: 调用 BM25 检索
    # 这里暂时返回空列表，后续实现 BM25 检索
    keyword_chunks = []
    
    # 6. 写入 state
    state["keyword_chunks"] = keyword_chunks
    
    logger.info(f"关键词检索完成：{rewritten_query} → {len(keyword_chunks)} 条结果")
    
    return state


if __name__ == "__main__":
    # 本地测试
    mock_state = {
        "session_id": "test-001",
        "rewritten_query": "P0A0F故障码是什么意思？",
        "extracted_entities": {
            "fault_codes": "P0A0F",
        },
    }
    
    result = search_by_keywords(mock_state)
    print(f"关键词检索结果：{len(result.get('keyword_chunks', []))} 条")
