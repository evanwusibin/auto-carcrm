# service_keyword_search BM25检索服务

> 文档编号：DOC-QUERY-SERVICE-03 | 版本：v1.0 | 更新时间：2026-06-13

---

## 一、服务目的

**用BM25算法进行关键词检索，补充向量检索可能漏掉的精确匹配。**

---

## 二、核心函数

```python
def search_by_keywords(state: QueryGraphState) -> QueryGraphState:
    """BM25关键词检索"""
    rewritten_query = state.get("rewritten_query")
    item_names = state.get("item_names", [])
    
    # 1. 从MongoDB读取chunks
    chunks = knowledge_repository.find_by_item_names(item_names)
    
    # 2. 构建BM25索引
    bm25 = build_bm25_index(chunks)
    
    # 3. 检索
    scores = bm25.get_scores(rewritten_query.split())
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
    
    keyword_chunks = [chunks[i] for i in top_indices]
    
    state["keyword_chunks"] = keyword_chunks
    return state
```

---

## 三、输入输出

| 维度 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 输入 | rewritten_query | str | 改写后的问题 |
| 输入 | item_names | list[str] | 主体名称列表 |
| 输出 | keyword_chunks | list[dict] | BM25检索结果 |

---

## 四、关键代码位置

- 服务：`app/rag/query/keyword_search_service.py`

---

*文档版本：v1.0 | 更新时间：2026-06-13*
