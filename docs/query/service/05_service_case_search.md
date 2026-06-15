# service_case_search 案例检索服务

> 文档编号：DOC-QUERY-SERVICE-05 | 版本：v1.1 | 更新时间：2026-06-13

---

## 一、服务目的

**从 Milvus 向量库中检索包含案例/故障/维修等关键词的知识切片**，优先返回与用户问题匹配的案例型内容。

---

## 二、核心函数

```python
@step_log("search_cases")
def search_cases(state: QueryGraphState) -> QueryGraphState:
    """
    案例检索：
    1. 从 state 获取 item_names、rewritten_query
    2. 从 Milvus kb_chunks 集合中查询候选切片
    3. 用案例关键词（案例/故障/维修/处理/现象/原因/解决/排查）加权
    4. 返回标准化 case_chunks 列表
    """
    item_names, rewritten_query = validate_case_search_state(state)
    state["case_chunks"] = search_case_chunks(item_names, rewritten_query)
    return state
```

---

## 三、输入输出

| 维度 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 输入 | item_names | list[str] | 主体名称列表 |
| 输入 | rewritten_query | str | 改写后的查询 |
| 输出 | case_chunks | list[dict] | 案例检索结果，含 title/content/score/type |

---

## 四、匹配策略

1. 从 Milvus 按 item_names 过滤，拉取 300 条候选
2. 对每条候选做关键词命中计数
3. 命中案例关键词时额外 ×1.5 加权
4. 不含案例关键词的候选直接跳过
5. 按分数降序取 Top 5

---

## 五、关键代码位置

- 服务：`app/rag/query/case_search_service.py`
- 节点：`app/process/query/agent/nodes/node_case_search.py`
- 向量库：`app/infra/vectorstore/milvus_gateway.py`

---

*文档版本：v1.1 | 更新时间：2026-06-13*
