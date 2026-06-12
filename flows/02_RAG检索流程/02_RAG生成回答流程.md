# RAG 生成回答流程

> 流程编号：FLOW-02-02 | 版本：v1.0 | 更新时间：2026-06-12

---

## 完整流程图

```mermaid
flowchart TD
    A[检索完成<br/>获得 Top-K 候选资料] --> B[按相关性排序]
    B --> C[选择最终上下文<br/>Top-5 Chunk]

    C --> D[组装 Prompt]

    D --> D1[System Prompt<br/>角色设定 + 约束规则]
    D --> D2[车辆信息<br/>车型/VIN/里程/购车日期]
    D --> D3[保养记录摘要<br/>上次保养时间/里程]
    D --> D4[质保规则摘要<br/>部件/年限/里程]
    D --> D5[检索到的知识片段<br/>手册/案例文本]
    D --> D6[用户原始问题<br/>+ 多轮历史对话]

    D1 --> E[调用大语言模型]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E
    D6 --> E

    E --> F[流式/非流式生成]
    F --> G[答案后处理]

    G --> G1{答案校验}
    G1 -- 包含无依据结论 --> G2[追加免责说明]
    G1 -- 涉及质保承诺 --> G3[改为预判表述<br/>初步预判/建议确认]
    G1 -- 涉及安全风险 --> G4[标注安全警示]
    G1 -- 答案正常 --> H[绑定引用来源]

    G2 --> H
    G3 --> H
    G4 --> H

    H --> H1[提取使用的 Chunk ID]
    H1 --> H2[查询对应文档元数据]
    H2 --> H3[构建引用列表<br/>文档名/章节/页码/版本]

    H3 --> I[构建最终响应]
    I --> I1[答案正文]
    I --> I2[引用来源列表]
    I --> I3[建议动作<br/>是否需要报修/预约]
    I --> I4[风险提示<br/>如有安全风险]

    I1 --> J[返回给用户]
    I2 --> J
    I3 --> J
    I4 --> J

    J --> K[记录问答日志]
    K --> K1[保存 qa_messages]
    K --> K2[保存 qa_references]
    K --> K3[更新 qa_sessions]
```

---

## Prompt 模板设计

### System Prompt（固定）

```
你是比亚迪商用车售后智能助手，负责基于企业内部知识库回答售后服务相关问题。

【核心约束】
1. 只能基于【参考资料】中的内容回答，不得编造政策、参数、配置或维修步骤
2. 参考资料不足时，明确告知"当前资料中未找到足够依据，建议联系授权服务站确认"
3. 涉及质保结论时，使用"初步预判"表述，提示最终以服务站检测为准
4. 涉及安全风险时（高压系统/制动故障/电池热失控等），必须在答案开头明确警示
5. 不得给出"保修""不保修"的最终结论，只能给出预判和建议

【输出格式】
- 第一行：直接结论（1-2句）
- 主体：依据说明（引用参考资料，说明来源）
- 结尾：注意事项 / 建议动作（如有风险或需人工确认）
```

### User Prompt 模板

```python
USER_PROMPT_TEMPLATE = """
【用户问题】
{question}

【车辆信息】
- 车型：{vehicle_model}
- VIN：{vin}
- 购车日期：{purchase_date}
- 当前里程：{current_mileage} km

【最近保养记录】
{maintenance_summary}

【参考资料】
{context}

请根据以上信息回答用户问题：
"""
```

### Context 格式

```python
def format_context(chunks: list) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        part = f"""【资料{i}】来源：{meta.get('doc_name', '未知')} / {meta.get('section_title', '')} / 第{meta.get('page_no', '?')}页（版本：{meta.get('version', '?')}，生效：{meta.get('effective_date', '?')}）
{chunk['chunk_text']}"""
        context_parts.append(part)
    return "\n\n".join(context_parts)
```

---

## 答案引用溯源展示格式

前端展示时，答案下方需展示引用卡片：

```
📄 参考来源 1
文档：T5轻卡质保手册 v1.0
章节：三电系统质保说明（第18页）
生效时间：2026-01-01
原文片段："动力电池质保期限为5年或20万公里（以先到者为准）……"
```

---

*流程版本：v1.0 | 更新时间：2026-06-12*
