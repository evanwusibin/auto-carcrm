# node_metadata_filter 元数据过滤

> 文档编号：DOC-QUERY-NODE-06 | 版本：v1.0 | 更新时间：2026-06-13

---

## 一、节点目的

**根据车型、版本、有效期等元数据过滤检索结果，确保结果与用户场景匹配。**

---

## 二、流程图

```
输入 state（含 rrf_chunks, entities）
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 获取参数                                                          │
│    rrf_chunks = state.get("rrf_chunks", [])                         │
│    entities = state.get("entities", {})                             │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. 构建过滤条件                                                      │
│    vehicle_model = entities.get("vehicle_model")                    │
│    doc_version = entities.get("doc_version")                        │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. 过滤结果                                                          │
│    filtered = []                                                    │
│    for chunk in rrf_chunks:                                         │
│        if vehicle_model and chunk.metadata.vehicle_model != ...:    │
│            continue                                                 │
│        if chunk.metadata.valid_until < today:                       │
│            continue                                                 │
│        filtered.append(chunk)                                       │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. 写入 state                                                       │
│    state["filtered_chunks"] = filtered                              │
│    return state                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、输入输出

| 维度 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 输入 | rrf_chunks | list[dict] | RRF融合结果 |
| 输入 | entities | dict | 抽取的实体 |
| 输出 | filtered_chunks | list[dict] | 过滤后的结果 |

---

## 四、与原项目差异

| 对比项 | 原项目 | 改造后 |
|--------|--------|--------|
| 过滤逻辑 | 无 | 新增，按车型/版本/有效期过滤 |
| 用途 | 无 | 确保结果与用户场景匹配 |

---

## 五、关键代码位置

- 节点：`app/process/query/agent/nodes/node_metadata_filter.py`
- 服务：`app/rag/query/metadata_filter_service.py`

---

*文档版本：v1.0 | 更新时间：2026-06-13*
