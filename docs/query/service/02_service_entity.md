# service_entity 实体抽取服务

> 文档编号：DOC-QUERY-SERVICE-02 | 版本：v1.0 | 更新时间：2026-06-13

---

## 一、服务目的

**从用户提问中抽取结构化实体，用于后续过滤和查询。**

---

## 二、核心函数

```python
def extract_entities(state: QueryGraphState) -> QueryGraphState:
    """抽取实体"""
    original_query = state.get("original_query")
    
    # 1. 调用LLM
    llm = llm_provider.chat()
    prompt = load_prompt("entity_extraction", query=original_query)
    response = llm.invoke(prompt)
    
    # 2. 解析JSON
    entities = parse_entities(response.content)
    
    state["entities"] = entities
    return state
```

---

## 三、输入输出

| 维度 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 输入 | original_query | str | 用户原始问题 |
| 输出 | entities | dict | 抽取的实体 |

---

## 四、实体类型

| 实体 | 说明 | 示例 |
|------|------|------|
| vehicle_model | 车型 | "东风天龙KL" |
| vin | 车架号 | "LGHXG6LC5NV123456" |
| fault_code | 故障码 | "P0101" |
| mileage | 里程 | "5万公里" |
| component | 部件 | "发动机" |
| time_expr | 时间 | "去年买的" |

---

## 五、关键代码位置

- 服务：`app/rag/query/entity_service.py`
- Prompt：`app/resources/prompts/entity_extraction.prompt`

---

*文档版本：v1.0 | 更新时间：2026-06-13*
