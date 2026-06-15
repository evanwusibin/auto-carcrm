# service_structured_query 结构化查询服务

> 文档编号：DOC-QUERY-SERVICE-04 | 版本：v1.1 | 更新时间：2026-06-13

---

## 一、服务目的

**从 MongoDB 知识文档元数据中检索结构化信息**，根据用户问题和实体抽取结果（车型、文档类型等），匹配最相关的知识文档记录。

---

## 二、核心函数

```python
@step_log("query_structured_data")
def query_structured_data(state: QueryGraphState) -> QueryGraphState:
    """
    结构化查询：
    1. 从 state 获取 item_names、rewritten_query、extracted_entities
    2. 按 item_names 从 MongoDB 查出知识文档
    3. 对文档元数据做关键词 + 实体匹配打分
    4. 返回标准化 structured_chunks 列表
    """
    item_names, rewritten_query, extracted_entities = validate_structured_query_state(state)
    state["structured_chunks"] = search_structured_documents(item_names, rewritten_query, extracted_entities)
    return state
```

---

## 三、输入输出

| 维度 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 输入 | item_names | list[str] | 主体名称列表 |
| 输入 | rewritten_query | str | 改写后的查询 |
| 输入 | extracted_entities | dict | 抽取的实体（vehicle_model/doc_type） |
| 输出 | structured_chunks | list[dict] | 结构化查询结果，含 title/item_name/content/score/type |

---

## 四、匹配策略

1. 关键词命中：将 rewritten_query 分词后，在文档元数据中统计命中次数
2. 实体加分：vehicle_model 和 doc_type 匹配时额外 +2 分
3. 按分数降序取 Top 5

---

## 五、关键代码位置

- 服务：`app/rag/query/structured_query_service.py`
- 节点：`app/process/query/agent/nodes/node_structured_query.py`
- 数据源：`app/infra/persistence/knowledge_repository.py`

---

*文档版本：v1.1 | 更新时间：2026-06-13*
