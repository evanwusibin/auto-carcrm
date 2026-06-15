# service_metadata_filter 元数据过滤服务

> 文档编号：DOC-QUERY-SERVICE-06 | 版本：v1.0 | 更新时间：2026-06-13

---

## 一、服务目的

**根据车型、版本、有效期等元数据过滤检索结果。**

---

## 二、核心函数

```python
def filter_by_metadata(state: QueryGraphState) -> QueryGraphState:
    """元数据过滤"""
    rrf_chunks = state.get("rrf_chunks", [])
    entities = state.get("entities", {})
    
    vehicle_model = entities.get("vehicle_model")
    today = datetime.now().strftime("%Y-%m-%d")
    
    filtered = []
    for chunk in rrf_chunks:
        # 车型过滤
        if vehicle_model and chunk.get("vehicle_model") != vehicle_model:
            continue
        # 有效期过滤
        if chunk.get("valid_until") and chunk["valid_until"] < today:
            continue
        filtered.append(chunk)
    
    state["filtered_chunks"] = filtered
    return state
```

---

## 三、输入输出

| 维度 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 输入 | rrf_chunks | list[dict] | RRF融合结果 |
| 输入 | entities | dict | 抽取的实体 |
| 输出 | filtered_chunks | list[dict] | 过滤后的结果 |

---

## 四、关键代码位置

- 服务：`app/rag/query/metadata_filter_service.py`

---

*文档版本：v1.0 | 更新时间：2026-06-13*
