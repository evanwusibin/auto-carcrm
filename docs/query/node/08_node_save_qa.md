# node_save_qa QA落库

> 文档编号：DOC-QUERY-NODE-08 | 版本：v1.0 | 更新时间：2026-06-13

---

## 一、节点目的

**保存问答记录到MongoDB，支持历史查询和数据分析。**

---

## 二、流程图

```
输入 state（含 session_id, original_query, answer, citations, entities）
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 获取参数                                                          │
│    session_id = state.get("session_id")                             │
│    original_query = state.get("original_query")                     │
│    answer = state.get("answer")                                     │
│    citations = state.get("citations", [])                           │
│    entities = state.get("entities", {})                             │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. 保存QA记录                                                        │
│    qa_record = {                                                    │
│        "session_id": session_id,                                    │
│        "query": original_query,                                     │
│        "answer": answer,                                            │
│        "citations": citations,                                      │
│        "entities": entities,                                        │
│        "timestamp": datetime.now()                                  │
│    }                                                                │
│    qa_repository.save(qa_record)                                    │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. 写入 state                                                       │
│    return state                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、输入输出

| 维度 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 输入 | session_id | str | 会话ID |
| 输入 | original_query | str | 用户原始问题 |
| 输入 | answer | str | 生成的答案 |
| 输入 | citations | list[dict] | 引用来源 |
| 输入 | entities | dict | 抽取的实体 |

---

## 四、与原项目差异

| 对比项 | 原项目 | 改造后 |
|--------|--------|--------|
| 历史存储 | MongoDB对话历史 | 增加QA会话表+引用表 |
| 存储内容 | 只有问答文本 | 增加实体+引用+置信度 |

---

## 五、关键代码位置

- 节点：`app/process/query/agent/nodes/node_save_qa.py`
- 服务：`app/rag/query/answer_service.py`

---

*文档版本：v1.0 | 更新时间：2026-06-13*
