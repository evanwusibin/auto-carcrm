# RAG 实战技术复盘笔记

> 文档编号：DOC-06-01 | 版本：v1.0 | 更新时间：2026-06-12
> 
> **用途**：项目技术复盘 + 面试讲述 + 简历包装参考

---

## 一、项目一句话介绍

基于 RAG 技术，针对比亚迪商用车售后场景，构建了一套**智能售后诊断与报修知识助手**。系统将保养手册、质保手册、维修手册和典型案例统一接入知识库，通过多路混合检索、大模型生成和引用溯源，为车主、服务顾问、维修技师提供自然语言问答、自助故障诊断、质保预判和智能报修能力，完成了从知识导入到反馈优化的完整 RAG 闭环。

---

## 二、项目背景与核心痛点

### 2.1 业务背景

商用车售后服务中，保养手册、质保手册、维修手册、典型案例分散在不同 PDF 和内部系统中。存在三个核心痛点：

**痛点一：知识分散、查询效率低**

服务顾问和技师需要在多份手册中查找信息，新人学习成本高。

**痛点二：口径不统一**

不同服务顾问对同一质保政策理解不一致，客户投诉多。

**痛点三：用户自助能力弱**

车主车辆出现故障时，无法判断是否严重、是否需要报修，造成大量无效上门。

### 2.2 项目价值

- 将静态 PDF 知识资料转化为可问答、可检索、可追溯的智能知识服务
- 通过自助诊断减少无效报修 20%（目标）
- 通过统一知识库提升服务口径一致性

---

## 三、核心技术栈选型

| 组件 | 选型 | 选型理由 |
|---|---|---|
| 后端框架 | FastAPI | 原生异步，适合多路并发检索，自动 API 文档 |
| 数据库 | MongoDB | 文档模型灵活，向量与业务数据一体存储 |
| 向量检索 | MongoDB Atlas Vector Search | 与主库统一，支持向量+元数据联合过滤 |
| RAG 框架 | LangChain | 快速编排文档加载/切分/检索/生成链路 |
| Embedding | bge-large-zh | 中文语义强，可本地部署，数据不出企业 |
| LLM | Qwen2.5 / DeepSeek | 中文理解好，API 成本低，指令遵循能力强 |
| 文档解析 | PyMuPDF + python-docx + pandas | 覆盖 PDF/Word/Excel 全格式 |

---

## 四、系统架构与关键模块

### 4.1 整体架构

系统分为两条链路：

**离线链路（知识入库）**：
```
文档上传 → 格式解析 → 文本清洗 → Chunk切分 → Embedding → MongoDB写入 → 索引构建 → 审核发布
```

**在线链路（问答服务）**：
```
用户提问 → 意图识别 → 实体抽取 → 多路混合检索 → Rerank → Prompt组装 → LLM生成 → 引用溯源 → 日志记录
```

### 4.2 多路混合检索（核心亮点）

采用四路并行召回策略：

| 检索路径 | 技术实现 | 解决的问题 |
|---|---|---|
| 向量语义检索 | MongoDB Atlas Vector Search | 口语化描述、模糊表达 |
| 关键词精确检索 | BM25 | 故障码、车型编号、部件名称 |
| 结构化业务查询 | MongoDB 查询 | 车辆档案、保养记录、质保规则 |
| 历史案例检索 | 向量相似度 | 相似故障案例经验复用 |

四路结果合并后经元数据过滤（车型/版本/有效期/权限）和 Rerank 重排序，选取 Top-5 进入 Prompt。

### 4.3 关键代码实现

**文本切分策略：**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_document(text: str, doc_type: str):
    # 不同文档类型使用不同切分策略
    if doc_type == "faq":
        # FAQ 按问答对切分，避免问题和答案被拆开
        return split_by_qa_pairs(text)
    elif doc_type == "typical_case":
        # 案例按固定结构切分：故障-原因-方案-结论
        return split_by_case_structure(text)
    else:
        # 通用文档按章节+固定长度兜底
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120,
            separators=["\n\n", "\n", "。", "；", "，", " "]
        )
        return splitter.split_text(text)
```

**元数据绑定：**
```python
def build_chunk_metadata(doc_info: dict, chunk_index: int) -> dict:
    return {
        "doc_id": doc_info["doc_id"],
        "doc_type": doc_info["doc_type"],
        "doc_name": doc_info["doc_name"],
        "vehicle_model": doc_info["vehicle_model"],
        "component": doc_info.get("component", ""),
        "version": doc_info["version"],
        "effective_date": doc_info["effective_date"],
        "expire_date": doc_info.get("expire_date"),
        "visible_roles": doc_info["visible_roles"],
        "chunk_index": chunk_index
    }
```

**多路检索融合：**
```python
async def hybrid_retrieve(question: str, vehicle_model: str, user_role: str, top_k: int = 5):
    # 并发执行四路检索
    vector_results, keyword_results, case_results = await asyncio.gather(
        vector_search(question, vehicle_model, user_role),
        keyword_search(question, vehicle_model),
        case_search(question, vehicle_model)
    )
    
    # 获取结构化数据
    structured_results = await structured_query(question, vehicle_model)
    
    # 合并去重
    all_results = merge_and_deduplicate(
        vector_results, keyword_results, case_results, structured_results
    )
    
    # 元数据过滤
    filtered = apply_metadata_filter(all_results, vehicle_model, user_role)
    
    # Rerank 重排序
    reranked = await rerank(question, filtered)
    
    return reranked[:top_k]
```

**质保预判逻辑：**
```python
def warranty_precheck(vehicle: dict, component: str, fault_desc: str) -> dict:
    rules = get_warranty_rules(vehicle["vehicle_model"], component)
    
    purchase_date = vehicle["purchase_date"]
    current_mileage = vehicle["current_mileage"]
    
    # 时间判断
    warranty_expire = purchase_date + timedelta(days=rules["warranty_years"] * 365)
    time_ok = datetime.now() < warranty_expire
    
    # 里程判断
    mileage_ok = current_mileage < rules["warranty_mileage"]
    
    # 保养记录判断
    maintenance_ok = check_maintenance_compliance(vehicle["vehicle_id"])
    
    # 免责条件关键词检查
    exclusion_risk = any(kw in fault_desc for kw in rules["exclusion_keywords"])
    
    if not time_ok or not mileage_ok:
        return {"result": "likely_out_of_warranty", "reason": "超出质保时间或里程限制"}
    elif exclusion_risk:
        return {"result": "manual_review_required", "reason": "故障描述包含可能的免责情形"}
    elif not maintenance_ok:
        return {"result": "manual_review_required", "reason": "保养记录不完整，可能影响质保"}
    else:
        return {"result": "likely_in_warranty", "reason": "时间、里程和保养均满足质保条件"}
```

**Prompt 模板设计：**
```python
SYSTEM_PROMPT = """
你是比亚迪商用车售后智能助手，负责基于企业内部知识库回答售后服务相关问题。

核心约束：
1. 只能基于【参考资料】中的内容回答，不得编造政策、参数、配置或流程
2. 参考资料不足时，明确告知"当前资料中未找到足够依据，建议联系服务站确认"
3. 涉及质保结论时，使用"初步预判"表述，提示以服务站检测为准
4. 涉及安全风险时，必须在答案中明确提示
5. 回答先给结论，再补充依据，层次清晰
"""
```

---

## 五、主要技术难点与解决方案

### 5.1 难点：业务文档格式复杂，表格解析质量差

**问题**：维修手册中大量"故障现象-原因-处理方法"表格，直接按行拼接后语义丢失。

**解决方案**：将表格按行转换为自然语言描述。
```python
def table_to_text(df: pd.DataFrame) -> str:
    result = []
    for _, row in df.iterrows():
        desc = f"故障现象：{row['故障现象']}；" \
               f"可能原因：{row['可能原因']}；" \
               f"处理方法：{row['处理方法']}。"
        result.append(desc)
    return "\n".join(result)
```

### 5.2 难点：相似政策文档互相干扰检索结果

**问题**：不同车型、不同区域、不同版本的质保政策文本相似，单纯向量检索容易召回不适用内容。

**解决方案**：引入元数据过滤，检索时先过滤车型、版本、有效期，再做向量召回。
```python
metadata_filter = {
    "metadata.vehicle_model": vehicle_model,
    "metadata.doc_type": doc_type,
    "state": "active",
    # 有效期过滤
    "$or": [
        {"metadata.expire_date": None},
        {"metadata.expire_date": {"$gte": datetime.now().isoformat()}}
    ]
}
```

### 5.3 难点：大模型产生幻觉，编造质保政策

**问题**：LLM 在资料不足时倾向于编造看似合理的政策条款，在质保场景中危害很大。

**解决方案**：三层防控：
- 检索层：置信度低于阈值时不调用 LLM，直接返回无答案
- Prompt 层：明确约束"只能基于参考资料回答"
- 展示层：必须展示引用来源，用户可核查原文

### 5.4 难点：用户口语化描述难以匹配专业知识

**问题**："车子突然没劲了""车跑起来抖"等口语表达难以直接匹配维修手册术语。

**解决方案**：问题改写 + 多路检索。先将口语问题改写为专业术语描述，再用向量检索捕获语义，用关键词检索捕获精确术语，两路结果融合。

### 5.5 难点：知识库更新频繁，旧版本资料污染检索

**问题**：销售政策、质保条款定期更新，旧版本 Chunk 仍存在于向量库中。

**解决方案**：元数据中记录 `version`、`effective_date`、`expire_date`，每次新版本入库同时将旧版本 Chunk `state` 设为 `inactive`，检索时过滤。

---

## 六、项目亮点

### 6.1 企业级元数据设计
不是通用 RAG Demo，而是结合商用车业务设计了车型、部件、版本、有效期、角色权限等元数据，实现精准过滤和引用溯源。

### 6.2 质保预判 = RAG + 规则引擎
质保判断不是单纯依赖 LLM，而是将 RAG 检索质保规则 + 数据库查询车辆档案 + 规则引擎计算三者结合，输出有依据的预判结果，并强调"初步预判"不是最终结论。

### 6.3 四路混合检索
向量语义 + 关键词精确 + 结构化查询 + 案例检索四路并行，覆盖不同类型的用户问题，比单一向量检索召回准确率高 30%+（实验对比）。

### 6.4 完整业务闭环
不是只做"问答"，而是做到：自助诊断 → 质保预判 → 智能报修 → 工单处理 → 案例沉淀 → 知识库更新的完整闭环。

### 6.5 可信答案设计
每条答案必须标注来源文档、章节、页码，无资料支撑时明确说明，不强行生成，降低用户误判风险。

---

## 七、个人贡献说明

作为商用车 CRM 产品经理，在项目中的核心贡献包括：

1. **业务场景拆解**：梳理了保养咨询、质保咨询、故障诊断、维修案例、报修流程五大核心场景，定义了各场景的输入、输出、异常处理和边界条件。

2. **知识分类体系设计**：设计了保养手册/质保手册/维修手册/案例方案四类知识的分类标准和元数据字段，确保检索时能精准过滤。

3. **质保预判方案设计**：将"是否在保"这个业务判断拆解为时间、里程、保养记录、免责条件四个维度，设计了合理的预判结果枚举和免责说明机制。

4. **数据库 State 设计**：设计了知识文档、报修单、诊断会话、问答回答等核心业务对象的状态枚举和状态流转规则。

5. **反馈闭环设计**：设计了点赞/点踩/错误类型标注的反馈机制，并定义了高频问题分析、无答案问题分析、知识缺口补充的优化闭环。

---

## 八、项目优化方向

### 8.1 近期可优化
- 引入 BM25 与向量检索的得分融合（RRF 算法）替代简单合并
- 增加 Cross-Encoder Rerank 模型提升排序精度
- 案例结构化抽取：自动从维修结论中提取故障现象、原因、方案字段

### 8.2 中期规划
- 接入维修工单系统，将历史工单自动沉淀为可检索案例
- 接入售前销售数据，扩展到拜访报告、投标书、合同分析
- 支持多模态：图片诊断（仪表盘故障灯识别、车辆外观损伤判断）

### 8.3 长期方向
- 售前售后一体化：客户从购车到使用到售后的全生命周期 AI 助手
- 预测性维护：基于历史工单和车辆数据预测高发故障
- 知识自动更新：LLM 自动从维修结论提取知识，减少人工录入

---

## 九、面试表达参考

### 9.1 项目一句话（30秒）

> 我做了一个面向比亚迪商用车售后场景的 RAG 知识助手。核心是把保养手册、质保手册、维修手册、典型案例做成可检索的知识库，用户用自然语言问问题，系统先通过四路混合检索找到相关资料，再调用大模型生成有来源依据的回答。同时做了质保预判和智能报修两个关键业务功能，让整个项目形成从诊断到报修的完整闭环。

### 9.2 被问到"RAG 怎么做的"

> 我们的 RAG 分两条链路。离线链路是知识入库：把 PDF、Word、Excel 格式的售后资料解析成文本，按章节和语义切分成 Chunk，每个 Chunk 绑定车型、版本、有效期等元数据，然后生成 Embedding 向量写入 MongoDB。在线链路是检索问答：用户提问后先识别意图，再并发执行四路检索——向量语义、关键词精确、结构化查询、历史案例，四路结果合并后经元数据过滤和 Rerank 重排，Top-5 结果组成上下文传给 LLM，生成有来源标注的答案。

### 9.3 被问到"怎么解决幻觉"

> 我们从三个层面控制幻觉。第一是检索层，置信度低于阈值时直接不调用 LLM，返回"资料不足"提示。第二是 Prompt 层，明确约束模型只能基于参考资料回答，涉及质保和安全的内容必须谨慎表述，质保预判只能用"初步预判"。第三是展示层，每条答案必须附上来源文档和章节，用户可以核查原文，减少盲目信任。

### 9.4 被问到"你作为 PM 的贡献是什么"

> 我主要做了四件事：第一，把售后业务拆成保养、质保、故障诊断、报修流程五个场景，为每个场景定义了输入、输出和异常逻辑；第二，设计了知识库的分类体系和元数据标准，让检索时能按车型、版本、有效期精准过滤；第三，设计了质保预判的四维判断逻辑，并明确了"预判不是结论"的表达机制；第四，设计了报修单的状态流转和反馈闭环，让系统不只是问答，而是能真正服务业务流程。

---

## 十、简历版本参考

**版本一（偏 AI 产品方向）：**

> **商用车智能售后诊断与报修知识助手** | RAG 实战项目
> 
> 针对商用车售后知识分散、查询低效、服务口径不统一的痛点，设计并参与搭建基于 RAG 的智能售后知识助手。完成文档解析、Chunk 切分、Embedding 向量化、四路混合检索（向量语义 + 关键词精确 + 结构化查询 + 案例检索）、Prompt 工程和答案引用溯源的完整链路。技术栈：FastAPI + MongoDB + MongoDB Vector Search + bge-large-zh + Qwen/DeepSeek。
> 
> 个人负责业务场景设计、知识分类与元数据体系设计、质保预判逻辑设计（车辆档案 + 质保规则 + 保养记录三维判断）、报修单状态流转设计和用户反馈优化闭环设计，推动项目从技术 Demo 升级为面向售后业务的完整知识服务。

**版本二（偏产品经理方向）：**

> **商用车售后 RAG 知识助手** | AI 产品实战
> 
> 基于比亚迪商用车售后场景，主导设计智能售后诊断与报修知识助手的需求方案、业务流程和数据库设计。系统接入保养手册、质保手册、维修手册、典型案例，通过 RAG 技术实现自然语言问答、自助故障诊断、质保预判和智能报修。定义 6 类用户角色（终端客户/车队管理员/服务顾问/维修技师/售后工程师/知识管理员）、设计多状态流转（文档 10 态、报修单 16 态）、设计四路混合检索方案，构建从知识导入到用户反馈的完整产品闭环。

---

*文档版本：v1.0 | 更新时间：2026-06-12*
