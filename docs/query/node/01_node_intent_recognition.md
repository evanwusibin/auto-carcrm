# node_intent_recognition 意图识别

> 文档编号：DOC-QUERY-NODE-01 | 版本：v1.0 | 更新时间：2026-06-13

---

## 一、节点目的

**识别用户提问的意图类型，决定后续走什么流程（检索/直接回答/调用API）。**

---

## 二、流程图

```
输入 state（含 original_query, history）
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 获取参数                                                          │
│    original_query = state.get("original_query")                     │
│    history = state.get("history", [])                               │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. 拼接历史上下文                                                    │
│    history_text = build_history_context(history)                    │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. 调用LLM识别意图                                                   │
│    intent = llm_provider.chat().invoke(                             │
│        load_prompt("intent_recognition",                            │
│                    query=original_query,                            │
│                    history=history_text)                            │
│    )                                                                │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. 写入 state                                                       │
│    state["intent"] = intent                                         │
│    return state                                                     │
└─────────────────────────────────────────────────────────────────────┘
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

| 意图类型 | 说明 | 后续流程 |
|----------|------|----------|
| pre_sales | 售前咨询 | 走检索流程（售前Prompt） |
| after_sales | 售后服务 | 走检索流程（售后Prompt） |
| usage_guide | 用车指导 | 走检索流程（用车Prompt） |
| complaint | 投诉/情绪 | 直接LLM回答（高温度） |
| chitchat | 闲聊寒暄 | 直接LLM回答（高温度） |
| business | 业务办理 | 调用第三方API（暂写死） |

---

## 五、与原项目差异

| 对比项 | 原项目 | 改造后 |
|--------|--------|--------|
| 意图分类 | 无（只有item_name确认） | 6类意图分类 |
| Prompt | 通用Prompt | 按意图加载不同Prompt |
| 路由逻辑 | 无 | 根据意图走不同分支 |

---

## 六、关键代码位置

- 节点：`app/process/query/agent/nodes/node_intent_recognition.py`
- 服务：`app/rag/query/intent_service.py`
- Prompt：`app/resources/prompts/intent_recognition.prompt`

---

*文档版本：v1.0 | 更新时间：2026-06-13*
