# service_intent 意图识别服务

> 文档编号：DOC-QUERY-SERVICE-01 | 版本：v1.0 | 更新时间：2026-06-13

---

## 一、服务目的

**调用LLM识别用户提问的意图类型，返回6类意图之一。**

---

## 二、核心函数

```python
def recognize_intent(state: QueryGraphState) -> QueryGraphState:
    """识别用户意图"""
    original_query = state.get("original_query")
    history = state.get("history", [])
    
    # 1. 拼接历史上下文
    history_text = build_history_context(history)
    
    # 2. 调用LLM
    llm = llm_provider.chat()
    prompt = load_prompt("intent_recognition",
                        query=original_query,
                        history=history_text)
    response = llm.invoke(prompt)
    
    # 3. 解析意图
    intent = parse_intent(response.content)
    
    state["intent"] = intent
    return state
```

---

## 三、输入输出

| 维度 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 输入 | original_query | str | 用户原始问题 |
| 输入 | history | list[dict] | 历史对话记录 |
| 输出 | intent | str | 意图类型 |

---

## 四、意图分类

| 意图 | 说明 | 后续流程 |
|------|------|----------|
| pre_sales | 售前咨询 | 走检索（售前Prompt） |
| after_sales | 售后服务 | 走检索（售后Prompt） |
| usage_guide | 用车指导 | 走检索（用车Prompt） |
| complaint | 投诉/情绪 | 直接LLM回答（高温度） |
| chitchat | 闲聊寒暄 | 直接LLM回答（高温度） |
| business | 业务办理 | 调用第三方API |

---

## 五、与原项目差异

| 对比项 | 原项目 | 改造后 |
|--------|--------|--------|
| 意图分类 | 无 | 6类意图 |
| Prompt | 通用 | 按意图加载不同Prompt |

---

## 六、关键代码位置

- 服务：`app/rag/query/intent_service.py`
- Prompt：`app/resources/prompts/intent_recognition.prompt`

---

*文档版本：v1.0 | 更新时间：2026-06-13*
