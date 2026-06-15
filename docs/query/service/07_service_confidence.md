# service_confidence 置信度处理服务

> 文档编号：DOC-QUERY-SERVICE-07 | 版本：v1.0 | 更新时间：2026-06-13

---

## 一、服务目的

**计算检索结果的置信度，决定是否需要追问用户。**

---

## 二、核心函数

```python
def check_confidence(state: QueryGraphState) -> QueryGraphState:
    """置信度判断"""
    rrf_chunks = state.get("rrf_chunks", [])
    item_names = state.get("item_names", [])
    
    # 计算平均分数
    avg_score = sum(chunk.get("score", 0) for chunk in rrf_chunks[:3]) / max(len(rrf_chunks[:3]), 1)
    
    # 是否有主体
    has_item = len(item_names) > 0
    
    # 计算置信度
    confidence = avg_score * 0.8 + (0.2 if has_item else 0)
    
    # 判断是否需要追问
    needs_clarify = confidence < 0.6
    
    state["confidence"] = confidence
    state["needs_clarify"] = needs_clarify
    return state
```

---

## 三、输入输出

| 维度 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 输入 | rrf_chunks | list[dict] | RRF融合结果 |
| 输入 | item_names | list[str] | 主体名称列表 |
| 输出 | confidence | float | 置信度（0-1） |
| 输出 | needs_clarify | bool | 是否需要追问 |

---

## 四、关键代码位置

- 服务：`app/rag/query/confidence_service.py`

---

*文档版本：v1.0 | 更新时间：2026-06-13*
