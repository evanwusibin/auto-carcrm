# Auto-CarCRM：汽车售后 RAG Agent 与智能知识助手

> 面向汽车售后、维修诊断、质保政策、保养咨询和报修辅助场景的 RAG + Agent 项目。系统以 FastAPI 为后端入口，使用 LangGraph 编排多节点查询流程，结合 Milvus 向量检索、BM25 关键词检索、结构化查询、维修案例召回、HyDE 查询扩展、MCP 联网搜索、RRF 融合与重排序，构建可追溯、可扩展的汽车售后智能知识助手。

---

## 项目定位

传统 CRM 系统更多负责记录客户、工单和维修数据，但一线售后场景真正需要的是“能理解问题、能查知识、能给出可执行建议”的智能助手。

`auto-carcrm` 的目标是把汽车售后知识库、维修案例、故障码、质保/保养政策和外部联网信息组织成一条完整的智能问答链路：

```text
用户自然语言问题
  ↓
主体识别 / 意图识别 / 实体抽取
  ↓
多路召回：向量、关键词、结构化、案例、HyDE、Web Search
  ↓
RRF 融合 / Metadata Filter / Rerank / 置信度判断
  ↓
LLM 基于证据生成答案
  ↓
返回答案、引用、候选主体、风险提示和会话记录
```

它不是单纯调用大模型聊天，而是把业务知识、检索链路、图编排和多轮状态管理组合起来，解决售后知识查询中的准确性、可追溯性和上下文一致性问题。

---

## 核心业务场景

| 场景 | 说明 |
|---|---|
| 售后知识问答 | 查询故障处理、保养周期、质保政策、维修流程等知识 |
| 故障诊断辅助 | 根据故障现象、故障码、车型主体召回维修案例和诊断建议 |
| 智能报修辅助 | 根据用户描述生成报修信息，辅助服务站接单 |
| 多轮追问 | 当主体或置信度不足时，提示用户补充车型、故障现象等关键字段 |
| 联网兜底 | Milvus/本地知识库没有覆盖时，通过 MCP Web Search 获取外部信息 |
| 会话沉淀 | 保存用户问题、改写问题、主体、答案和引用，为后续上下文和评估服务 |

---

## 技术架构

```text
Frontend / Chat UI
  ↓ HTTP / SSE
FastAPI Router
  ↓
Page Service
  ↓
LangGraph Query Graph
  ├─ node_item_name_confirm      主体识别与问题改写
  ├─ node_intent_recognition     意图识别，闲聊/投诉可跳过检索
  ├─ node_entity_extraction      实体抽取
  ├─ node_search_embedding       Milvus 向量召回
  ├─ node_keyword_search         BM25/Jieba 关键词召回
  ├─ node_structured_query       结构化字段查询
  ├─ node_case_search            维修案例召回
  ├─ node_search_embedding_hyde  HyDE 假设性文档召回
  ├─ node_web_search_mcp         MCP 联网搜索
  ├─ node_rrf                    多路召回融合
  ├─ node_metadata_filter        元数据过滤
  ├─ node_rerank                 重排序
  ├─ node_confidence_check       置信度判断/追问
  ├─ node_answer_output          答案生成
  └─ node_save_qa                问答历史保存
  ↓
Infra Layer
  ├─ LLM Provider
  ├─ Milvus VectorStore
  ├─ MongoDB Repository
  ├─ MinIO Object Storage
  ├─ MinerU Document Parser
  └─ MCP Web Search
```

---

## 技术栈

| 模块 | 技术选型 | 作用 |
|---|---|---|
| Web 后端 | FastAPI + Uvicorn | HTTP API、SSE 流式响应、OpenAPI 文档 |
| 图编排 | LangGraph | 将查询链路拆成可观测、可路由、可扩展的节点 |
| LLM 接入 | LangChain + OpenAI-compatible API | 支持云模型、本地微调模型和统一 LLM Provider |
| 向量库 | Milvus / PyMilvus | 存储文档切片向量、主体向量和案例向量 |
| Embedding | BGE-M3 / FlagEmbedding | 中文语义检索，支持稠密/稀疏混合检索 |
| 关键词检索 | Jieba + rank-bm25 | 弥补纯向量对精确术语、故障码、型号召回不足 |
| 融合排序 | RRF + Rerank | 融合多路召回，提升最终证据质量 |
| 文档解析 | MinerU / magic-pdf | PDF/文档解析、知识导入、切片构建 |
| 数据库 | MongoDB | 文档状态、会话历史、业务数据和审计记录 |
| 对象存储 | MinIO | 原始文件、图片、解析产物等对象存储 |
| 联网检索 | MCP Web Search | 本地知识库无覆盖时联网兜底 |
| 前端 | HTML/CSS/JS + SSE | 聊天界面、流程进度、候选主体交互 |
| 工程管理 | uv / pyproject.toml | Python 依赖和锁文件管理 |

---

## 查询链路设计

### 1. 主体识别与问题改写

用户可能会问：

```text
这个车故障灯亮了怎么办？
它的保养周期是多少？
吃午饭了
```

系统会先执行主体识别和问题改写：

- 当前问题有明确车型/主体时，优先使用当前主体。
- 当前问题是代词指代时，从历史会话中继承主体。
- 识别到多个候选主体时，返回候选列表让用户确认。
- 没有汽车主体且本地知识库不适合回答时，设置 `need_web_search=True`，进入 MCP 联网搜索或通用回答分支。

这个设计避免了“所有问题都强行走 Milvus 汽车知识库”的错误路径。

### 2. 多路召回

系统不是只做单一路向量检索，而是并行使用多种召回方式：

| 召回方式 | 解决的问题 |
|---|---|
| 向量召回 | 语义相似问题、自然语言描述 |
| 关键词召回 | 故障码、车型型号、精确术语 |
| 结构化查询 | 车型、部件、故障码、政策字段等结构化条件 |
| 案例召回 | 历史维修案例与经验沉淀 |
| HyDE 召回 | 先生成假设性答案，再用答案语义检索相关资料 |
| Web Search | 本地知识库无覆盖或需要实时信息时兜底 |

### 3. 融合、过滤与重排序

多路召回后，系统通过 RRF 将不同来源结果融合，再经过元数据过滤和 rerank，提高最终上下文的相关性。

```text
embedding_chunks
keyword_chunks
structured_chunks
case_chunks
hyde_embedding_chunks
web_search_docs
  ↓
RRF merge
  ↓
metadata filter
  ↓
rerank
  ↓
confidence check
```

### 4. 置信度和追问

当召回结果不足、主体不明确或置信度低时，系统不会强行编答案，而是生成追问，例如让用户补充车型、故障码、故障现象、行驶里程等信息。

---

## 和 crm-finetune 的联动

`auto-carcrm` 可以使用云端 LLM，也可以接入 `crm-finetune` 项目部署出来的本地微调模型。

```text
crm-finetune
  └─ Qwen3-4B LoRA 微调
  └─ serve_openai.py 暴露 http://localhost:8100/v1
        ↓
auto-carcrm
  └─ .env 修改 OPENAI_BASE_URL / LLM_DEFAULT_MODEL
        ↓
所有 LLM 节点复用本地领域模型
```

示例配置：

```env
OPENAI_BASE_URL=http://localhost:8100/v1
OPENAI_API_KEY=not-needed
LLM_DEFAULT_MODEL=qwen3-crm
```

两者关系：

- RAG 负责事实检索、引用和证据组织。
- 微调模型负责更符合汽车售后语境的表达、格式和诊断话术。
- 私有化部署时可以减少对外部云模型的依赖。

---

## 目录结构

```text
auto-carcrm/
├── app/
│   ├── api/                       # FastAPI 路由和 Schema
│   ├── core/                      # 依赖、响应、异常、中间件
│   ├── domain/                    # 业务服务
│   ├── infra/                     # LLM、Milvus、MongoDB、MinIO、文档解析等基础设施
│   ├── process/
│   │   ├── import_/               # 知识导入流程：页面层、图编排、节点
│   │   └── query/                 # 查询流程：页面层、LangGraph、RAG 节点
│   ├── rag/                       # RAG 业务能力实现
│   ├── resources/                 # HTML 页面和提示词资源
│   └── main.py                    # 后端统一启动入口
├── docs/                          # 需求、架构、数据库、接口和技术复盘文档
├── flows/                         # Mermaid 流程图
├── tests/                         # 测试用例
├── docker-compose.milvus.yml      # 本地 Milvus 依赖
├── pyproject.toml                 # Python 项目依赖
├── uv.lock                        # uv 锁文件
└── README.md
```

---

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate
uv sync
```

如果不用 uv，也可以根据 `pyproject.toml` 手动安装依赖。

### 2. 配置环境变量

```bash
copy .env.example .env
```

按实际情况配置：

- LLM API 地址和模型名
- MongoDB 连接
- Milvus 地址
- MinIO 地址
- MCP Web Search 地址和 API Key
- Embedding/Rerank 配置

注意：`.env` 只用于本地运行，不能提交到 GitHub。

### 3. 启动依赖服务

```bash
docker compose -f docker-compose.milvus.yml up -d
```

MongoDB、MinIO 等按你的本地环境或 Docker 配置启动。

### 4. 启动后端

```bash
python app/main.py
```

默认访问：

```text
http://localhost:8000/docs
```

### 5. 打开聊天页面

项目内置了前端聊天页面，位于：

```text
app/resources/html/chat.html
```

可以通过后端路由或静态页面方式访问，具体以当前路由配置为准。

---

## 关键设计亮点

### 1. LangGraph 节点化查询链路

每个阶段都被拆成独立节点，便于调试、观测和扩展。比如主体确认失败可以提前返回候选主体，闲聊/投诉可以跳过检索，非库内信息可以走 MCP 搜索。

### 2. 多路召回而不是单向量检索

汽车售后场景里有大量型号、故障码和部件名，单纯向量检索容易漏召回。项目同时引入关键词、结构化、案例、HyDE 和联网搜索，提升覆盖率。

### 3. Web Search 兜底

当本地 Milvus 没有信息、主体无法识别或问题超出本地知识库时，系统可以走 MCP Web Search，再由答案节点基于搜索结果生成回答。

### 4. 主体识别和候选确认

车型/产品主体是售后知识问答的关键上下文。系统会结合当前问题和历史会话确认主体，必要时返回候选主体让用户选择，避免错误继承上下文。

### 5. 可切换云模型和本地微调模型

通过 OpenAI 兼容接口抽象 LLM Provider，既能接云端模型，也能接 `crm-finetune` 部署的本地 Qwen3-CRM 模型。

---

## 项目边界

- 这是教学/实战项目，不包含完整企业生产权限体系、灰度发布和多租户治理。
- 本地 `.env`、日志、解析产物、截图和临时备份不应进入 GitHub。
- RAG 回答质量依赖知识库质量、切片策略、召回配置和 LLM 输出稳定性。
- 微调模型不能替代 RAG 的事实检索；二者是互补关系。

---

## 推荐仓库描述

> Automotive after-sales RAG Agent built with FastAPI, LangGraph, Milvus, MongoDB, BGE-M3, hybrid retrieval, RRF rerank, MCP web search, and optional integration with a Qwen3 LoRA fine-tuned local model.
