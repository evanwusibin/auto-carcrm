# 后端落地指南：`app/` 目录结构与运行配置

> 文档编号：DOC-07-01 | 版本：v1.1 | 更新时间：2026-06-12
> 适用项目：商用车智能售后诊断与报修知识助手（RAG）

---

## 一、目标与设计原则

本指南基于：

- 仓库内的 `app/` 模板代码（已有 `import` / `query` 两套 LangGraph 链路与 FastAPI 入口）
- `docs/` 项目文档（架构、技术栈、数据库、接口、状态机、RAG 复盘）
- `flows/` 流程图（数据导入、RAG 检索、业务流程、状态流转）

对 `app/` 目录进行「以 `docs/` 业务设计为主、对模板做吸收式优化」的落地改造，使得：

1. 知识库导入链路跑通：上传 → 解析 → 清洗 → 切块 → 向量化 → 写入 → 索引 → 审核发布
2. 在线问答链路跑通：提问 → 意图识别 → 实体抽取 → 四路混合检索 → 融合 → Rerank → Prompt → LLM → 引用溯源
3. 业务闭环跑通：车辆 → 诊断 → 质保预判 → 报修 → 案例沉淀
4. 全链路用 `.env` 统一配置；保留 `MongoDB + MinIO + BGE-M3 + bge-reranker + Qwen/DeepSeek` 的整体技术方向

> 本次更新说明：
> - 本文**不再要求 `app/` 完全贴合当前模板目录**。
> - 目录设计优先服从 `docs/` 和 `flows/` 里定义的业务链路、状态流转和接口边界。
> - 模板里成熟可复用的部分继续保留，例如：`LangGraph`、`BGE-M3`、`bge-reranker`、`MinIO`、`MinerU`、`SSE`、已有的日志与配置加载方式。
> - 向量库层建议做成**可替换适配层**。默认推荐按项目文档优先使用 `MongoDB Atlas Vector Search` 设计；如果你当前阶段想沿用模板里的 `Milvus`，只需要替换 `app/infra/vectorstore/` 实现，不影响上层服务与流程编排。

### 1.1 本文优化原则

1. **业务优先**：先对齐 `知识导入 -> RAG问答 -> 诊断 -> 质保预判 -> 报修 -> 案例沉淀` 的完整闭环，再看模板里哪些代码可以复用。
2. **分层清晰**：`api` 只处理 HTTP，`service/domain` 处理业务，`process` 处理图编排，`infra` 处理外部依赖。
3. **适配优于硬编码**：向量库、LLM、对象存储、文档解析都通过 gateway/provider 封装。
4. **模板吸收式改造**：不是推翻模板重写，而是保留已有价值模块，逐步替换不符合项目文档的部分。
5. **先跑通 MVP**：第一阶段先跑通 `知识导入 + RAG问答 + 引用溯源`，第二阶段补 `诊断/质保/报修`。

---

## 二、推荐的 `app/` 目录结构

> 这一版目录是 **`docs` 优先的优化版**，不是对当前模板目录的一比一映射。下面标注：
> - `保留`：模板可以直接复用
> - `调整`：模板保留，但职责要重构
> - `新增`：根据项目文档补齐

> 「✅ 已存在」= 模板里已有；「🆕 新增」= 需新建；「✏️ 改写」= 模板存在但需补齐业务能力。

```
auto-carcrm/
├── .env                              # ✅ 已存在（改名自 .env.example）
├── .env.example                      # ✅ 已存在
├── pyproject.toml                    # ✅ 已存在
├── uv.lock                           # ✅ 已存在
│
├── app/                              # ✅ 模板根目录
│   ├── __init__.py                   # ✅ 已存在
│   │
│   ├── api/                          # ✅ 已存在，接口层
│   │   ├── __init__.py               # ✅ 已存在
│   │   ├── http/                     # ✅ 已存在
│   │   │   ├── __init__.py           # ✅ 已存在
│   │   │   ├── import_server.py      # ✅ 已存在 → ✏️ 改写：挂载 /api/v1/knowledge 业务路由
│   │   │   ├── query_server.py       # ✅ 已存在 → ✏️ 改写：挂载 /api/v1/qa 业务路由
│   │   │   ├── vehicle_server.py     # 🆕 新增：车辆接口
│   │   │   ├── repair_server.py      # 🆕 新增：报修工单接口
│   │   │   ├── warranty_server.py    # 🆕 新增：质保预判接口
│   │   │   ├── diagnosis_server.py   # 🆕 新增：智能诊断接口
│   │   │   └── knowledge_admin_server.py  # 🆕 新增：知识库管理接口（CRUD/审核/发布）
│   │   │
│   │   └── schemas/                  # ✅ 已存在
│   │       ├── __init__.py           # ✅ 已存在
│   │       ├── import_schema.py      # ✅ 已存在 → ✏️ 改写：增 doc_type/vehicle_model 等字段
│   │       ├── query_schema.py       # ✅ 已存在 → ✏️ 改写：增 vehicle_id、intents、stream_mode
│   │       ├── vehicle_schema.py     # 🆕 新增
│   │       ├── repair_schema.py      # 🆕 新增
│   │       ├── warranty_schema.py    # 🆕 新增
│   │       ├── diagnosis_schema.py   # 🆕 新增
│   │       └── knowledge_schema.py   # 🆕 新增
│   │
│   ├── core/                         # 🆕 新增：核心能力（启动/依赖注入）
│   │   ├── __init__.py
│   │   ├── lifespan.py               # FastAPI 启动/关闭钩子
│   │   ├── dependencies.py           # 鉴权 / 角色 / 数据库注入
│   │   ├── exceptions.py             # 统一异常 & 错误码
│   │   └── response.py               # 统一响应结构 {code, message, data, timestamp}
│   │
│   ├── infra/                        # ✅ 已存在，基础设施
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── providers.py          # ✅ 已存在 → ✏️ 增加 vehicle / repair / warranty / diagnosis 业务配置
│   │   ├── document_parse/
│   │   │   ├── __init__.py
│   │   │   └── mineru_gateway.py     # ✅ 已存在
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   └── providers.py          # ✅ 已存在 → ✏️ 增加 embed_query/stream_chat
│   │   ├── object_stroage/
│   │   │   ├── __init__.py
│   │   │   └── minio_gateway.py      # ✅ 已存在
│   │   ├── persistence/              # ✅ 已存在（业务持久化）
│   │   │   ├── __init__.py
│   │   │   ├── history_repository.py # ✅ 已存在（聊天历史）
│   │   │   ├── knowledge_repository.py  # 🆕 新增：知识文档/Chunk 持久化
│   │   │   ├── vehicle_repository.py    # 🆕 新增
│   │   │   ├── repair_repository.py     # 🆕 新增
│   │   │   ├── warranty_repository.py   # 🆕 新增
│   │   │   ├── diagnosis_repository.py # 🆕 新增
│   │   │   ├── qa_repository.py        # 🆕 新增：QA 会话/消息/引用
│   │   │   └── case_repository.py      # 🆕 新增：典型案例
│   │   └── vectorstore/              # ✅ 已存在
│   │       ├── __init__.py
│   │       └── milvus_gateway.py     # ✅ 已存在 → ✏️ 增加 metadata 过滤能力
│   │
│   ├── process/                      # ✅ 已存在，图编排层（LangGraph）
│   │   ├── __init__.py
│   │   ├── import_/                  # 导入流程
│   │   │   ├── __init__.py
│   │   │   └── agent/
│   │   │       ├── __init__.py
│   │   │       ├── main_graph.py     # ✅ 已存在 → ✏️ 增加 doc_meta 节点、知识审核发布节点
│   │   │       ├── state.py          # ✅ 已存在 → ✏️ 增 vehicle_model/doc_type/version 等元数据
│   │   │       └── nodes/
│   │   │           ├── __init__.py
│   │   │           ├── node_entry.py
│   │   │           ├── node_pdf_to_md.py
│   │   │           ├── node_md_img.py
│   │   │           ├── node_document_split.py
│   │   │           ├── node_item_name_recognition.py
│   │   │           ├── node_bge_embedding.py
│   │   │           ├── node_import_milvus.py
│   │   │           ├── node_doc_meta.py          # 🆕 新增：元数据抽取（车型/版本/有效期/角色）
│   │   │           ├── node_save_knowledge.py    # 🆕 新增：写 knowledge_documents
│   │   │           └── node_publish.py           # 🆕 新增：审核发布切换 state
│   │   └── query/                    # 查询流程
│   │       ├── __init__.py
│   │       └── agent/
│   │           ├── __init__.py
│   │           ├── main_graph.py     # ✅ 已存在 → ✏️ 重写为「四路并行 + 业务融合」
│   │           ├── state.py          # ✅ 已存在 → ✏️ 增 vehicle_id/intent/extracted_entities/metadata_filter
│   │           └── nodes/
│   │               ├── __init__.py
│   │               ├── node_item_name_confirm.py
│   │               ├── node_search_embedding.py
│   │               ├── node_search_embedding_hyde.py
│   │               ├── node_web_search_mcp.py
│   │               ├── node_rrf.py
│   │               ├── node_rerank.py
│   │               ├── node_answer_output.py
│   │               ├── node_intent_recognition.py       # 🆕 新增：意图分类
│   │               ├── node_entity_extraction.py       # 🆕 新增：实体抽取（车型/VIN/故障码/里程）
│   │               ├── node_keyword_search.py          # 🆕 新增：BM25 关键词检索
│   │               ├── node_structured_query.py        # 🆕 新增：车辆档案/保养记录/质保规则
│   │               ├── node_case_search.py             # 🆕 新增：典型案例检索
│   │               ├── node_metadata_filter.py         # 🆕 新增：车型/版本/有效期/权限过滤
│   │               ├── node_confidence_check.py        # 🆕 新增：置信度判断 & 追问
│   │               └── node_save_qa.py                 # 🆕 新增：QA 会话/消息/引用落库
│   │
│   ├── rag/                          # ✅ 已存在，RAG 业务服务层
│   │   ├── __init__.py
│   │   ├── import_/                  # 导入 RAG 能力
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── embedding_service.py
│   │   │   ├── enrich_markdown_images.py
│   │   │   ├── entry_service.py
│   │   │   ├── index_service.py
│   │   │   ├── item_name_service.py
│   │   │   ├── pdf_parse_service.py
│   │   │   ├── split_service.py
│   │   │   ├── doc_meta_service.py           # 🆕 新增：元数据抽取
│   │   │   └── knowledge_persist_service.py  # 🆕 新增：知识文档/Chunk 持久化
│   │   └── query/                    # 查询 RAG 能力
│   │       ├── __init__.py
│   │       ├── answer_service.py
│   │       ├── embedding_search_service.py
│   │       ├── hyde_search_sevice.py
│   │       ├── item_name_confirm_service.py
│   │       ├── rerank_service.py
│   │       ├── rrf_service.py
│   │       ├── web_search_service.py
│   │       ├── keyword_search_service.py     # 🆕 新增：BM25
│   │       ├── structured_query_service.py   # 🆕 新增：车辆档案/保养/质保规则
│   │       ├── case_search_service.py        # 🆕 新增：典型案例
│   │       ├── metadata_filter_service.py    # 🆕 新增：车型/版本/有效期/权限
│   │       ├── confidence_service.py         # 🆕 新增：低置信度处理
│   │       └── prompt_builder.py             # 🆕 新增：系统提示词 + 业务上下文
│   │
│   ├── domain/                       # 🆕 新增：业务领域服务（不依赖 LangGraph）
│   │   ├── __init__.py
│   │   ├── diagnosis_service.py      # 智能诊断：四要素 → 风险等级 → 建议
│   │   ├── warranty_service.py       # 质保预判：RAG + 规则引擎
│   │   ├── maintenance_service.py    # 保养判断：记录+里程+规则
│   │   ├── repair_service.py         # 报修单：创建→派单→关单
│   │   └── case_service.py           # 案例沉淀：维修结论→结构化→审核→入库
│   │
│   ├── resources/                    # ✅ 已存在
│   │   ├── __init__.py
│   │   ├── html/
│   │   │   ├── chat.html             # ✅ 已存在
│   │   │   └── import.html           # ✅ 已存在
│   │   └── prompts/                  # ✅ 已存在
│   │       ├── answer_out.prompt          # ✅ 已存在 → ✏️ 改写：增加引用编号、风险提示
│   │       ├── hyde_prompt.prompt          # ✅ 已存在
│   │       ├── image_summary.prompt        # ✅ 已存在
│   │       ├── item_name_recognition.prompt# ✅ 已存在
│   │       ├── product_recognition_system.prompt
│   │       ├── rerank_text_refine.prompt   # ✅ 已存在
│   │       ├── rewritten_query_and_itemnames.prompt  # ✅ 已存在 → ✏️ 改写：融合车型/故障码等
│   │       ├── intent_recognition.prompt   # 🆕 新增
│   │       ├── entity_extraction.prompt    # 🆕 新增
│   │       ├── warranty_precheck.prompt    # 🆕 新增
│   │       └── diagnosis.prompt            # 🆕 新增
│   │
│   ├── shared/                       # ✅ 已存在，公共能力
│   │   ├── __init__.py
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── milvus_utils.py
│   │   │   ├── minio_utils.py
│   │   │   ├── mongo_history_utils.py
│   │   │   ├── mongo_business_utils.py  # 🆕 新增：业务库连接（含车辆/报修/质保/案例/QA）
│   │   │   └── mongo_knowledge_utils.py # 🆕 新增：knowledge_documents / chunks 库连接
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── bailian_mcp_config.py
│   │   │   ├── common.py
│   │   │   ├── embedding_config.py
│   │   │   ├── lm_config.py
│   │   │   ├── milvus_config.py
│   │   │   ├── mineru_config.py
│   │   │   ├── minio_config.py
│   │   │   ├── reranker_config.py
│   │   │   ├── settings_config.py
│   │   │   ├── business_config.py       # 🆕 新增：业务库名/角色/超时/阈值
│   │   │   └── rag_config.py            # 🆕 新增：chunk_size、top_k、置信度阈值等
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── embedding_utils.py
│   │   │   ├── lm_utils.py
│   │   │   ├── reranker_utils.py
│   │   │   └── stream_chat_utils.py     # 🆕 新增：LangChain 流式回调封装
│   │   ├── runtime/
│   │   │   ├── __init__.py
│   │   │   ├── load_prompt.py
│   │   │   └── logger.py
│   │   ├── tool/
│   │   │   ├── __init__.py
│   │   │   ├── download_bgem3.py
│   │   │   └── download_reranker.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── escape_milvus_string_utils.py
│   │       ├── format_utils.py
│   │       ├── normalize_sparse_vector.py
│   │       ├── path_util.py
│   │       ├── rate_limit_utils.py
│   │       ├── sse_utils.py
│   │       ├── task_utils.py
│   │       ├── time_utils.py            # 🆕 新增：质保期/保养周期计算
│   │       └── retry_utils.py           # 🆕 新增：LLM/Milvus 通用重试
│   │
│   └── main.py                       # 🆕 新增：统一入口（挂载所有路由/中间件/lifespan）
│
├── docs/                             # ✅ 文档（已就位）
│   └── 07_后端落地文档_app目录与运行指南.md  # 🆕 即本文
│
├── flows/                            # ✅ 流程图（已就位）
│
├── frontend/                         # ✅ 前端原型（已就位）
│
├── tests/                            # 🆕 新增：单元 & 集成测试
│   ├── test_import_graph.py
│   ├── test_query_graph.py
│   ├── test_warranty.py
│   ├── test_diagnosis.py
│   └── test_api.py
│
├── scripts/                          # 🆕 新增：运维脚本
│   ├── init_milvus_collections.py
│   ├── init_mongo_collections.py
│   └── seed_demo_data.py
│
├── docker/                           # 🆕 新增：Docker 镜像
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── output/                           # ✅ 已存在：上传文件落盘目录
└── logs/                             # ✅ 日志目录（logger 启动自动创建）
```

---

## 三、`.env` 文件（推荐最终版）

> 模板已有 `.env.example`，下面给出「**保留并扩写**」的最终内容。

```env
# =========================
# 应用基础配置
# =========================
IMPORT_APP_NAME=AutoCarCRM RAG Import Service
QUERY_APP_NAME=AutoCarCRM RAG Query Service
APP_ENV=dev
APP_HOST=0.0.0.0
IMPORT_APP_PORT=8000
QUERY_APP_PORT=8001
CORS_ORIGINS=*

# =========================
# LLM / VL 模型配置（兼容 OpenAI 协议）
# =========================
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-your-key
LLM_DEFAULT_MODEL=qwen-plus
LLM_VL_MODEL=qwen-vl-max
LLM_DEFAULT_TEMPERATURE=0.1
LLM_MAX_TOKENS=2048

# =========================
# Embedding（BGE-M3 稠密+稀疏）
# =========================
BGE_M3_PATH=./models/bge-m3
BGE_M3=BAAI/bge-m3
BGE_DEVICE=cuda
BGE_FP16=True
EMBEDDING_BATCH_SIZE=5

# =========================
# Reranker（bge-reranker-v2-m3）
# =========================
BGE_RERANKER_LARGE=./models/bge-reranker-v2-m3
BGE_RERANKER_DEVICE=cuda
BGE_RERANKER_FP16=True

# =========================
# Milvus 向量库
# =========================
MILVUS_URL=http://127.0.0.1:19530
CHUNKS_COLLECTION=kb_chunks
ENTITY_NAME_COLLECTION=kb_entities
ITEM_NAME_COLLECTION=kb_item_names
CASES_COLLECTION=kb_cases
MILVUS_VECTOR_DIM=1024
MILVUS_CHUNK_CONTENT_MAX_LENGTH=65535

# =========================
# MongoDB 业务库（聊天历史 / 业务对象 / 知识元数据）
# =========================
MONGO_URL=mongodb://127.0.0.1:27017
MONGO_DB_NAME=auto_carcrm
MONGO_KNOWLEDGE_DB=auto_carcrm_kb

# =========================
# MinIO 对象存储（图片 / 原始文件）
# =========================
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=auto-carcrm
MINIO_IMG_DIR=/kb-images
MINIO_FILE_DIR=/kb-files
MINIO_SECURE=False

# =========================
# MinerU 文档解析
# =========================
MINERU_BASE_URL=https://your-mineru-endpoint
MINERU_API_TOKEN=your-mineru-token
MINERU_MODEL_VERSION=vlm
MINERU_POLL_TIMEOUT_SECONDS=600
MINERU_POLL_INTERVAL_SECONDS=3
MINERU_DOWNLOAD_TIMEOUT_SECONDS=30

# =========================
# DashScope MCP / WebSearch
# =========================
MCP_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp

# =========================
# 业务阈值（RAG 召回/生成/质保/诊断）
# =========================
RAG_VECTOR_TOPK=20
RAG_KEYWORD_TOPK=10
RAG_CASE_TOPK=5
RAG_FINAL_TOPK=5
RAG_CONFIDENCE_THRESHOLD=0.55
RAG_RRF_K=60
RAG_MAX_CONTEXT_CHARS=10000

WARRANTY_DEFAULT_YEARS=5
WARRANTY_DEFAULT_MILEAGE=200000
DIAGNOSIS_RISK_HIGH_KEYWORDS=无法启动,冒烟,起火,异响,刹车失灵,动力中断,高压报警

# =========================
# Chunk 切分
# =========================
CHUNK_MAX_SIZE=1000
CHUNK_SIZE=600
CHUNK_OVERLAP=50

# =========================
# 日志
# =========================
LOG_CONSOLE_ENABLE=True
LOG_CONSOLE_LEVEL=INFO
LOG_FILE_ENABLE=True
LOG_FILE_LEVEL=INFO
LOG_FILE_RETENTION=7 days

# =========================
# JWT 鉴权
# =========================
JWT_SECRET=please-change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# =========================
# 项目根目录（可选，默认自动递归查找 .env）
# =========================
PROJECT_ROOT=
```

---

## 四、每个文件需要调整 / 新增的代码要点

> 下面按目录顺序列出，**「✏️ 改写」= 模板已有，需补齐能力；「🆕 新增」= 不存在，需新建**。代码片段只列关键点，不做整文件覆盖。

### 4.1 入口与配置层

#### `app/main.py` 🆕
- 用单一入口同时挂载 import / query / vehicle / repair / warranty / diagnosis / knowledge_admin 等所有路由（避免多进程启动混乱）
- 注册 `core.lifespan`：`on_startup` 时初始化 Milvus 集合、Mongo 索引、Embedding/Reranker 单例；`on_shutdown` 关闭连接
- 注册全局异常处理 `core.exceptions`
- 注册统一响应中间件 `core.response`

#### `app/core/lifespan.py` 🆕
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_milvus_collections()        # scripts/init_milvus_collections.py
    init_mongo_collections()         # scripts/init_mongo_collections.py
    get_bge_m3_ef()                  # 预热 embedding
    get_reranker_model()             # 预热 reranker
    get_minio_client()               # 预热 minio
    yield
    close_clients()
```

#### `app/core/response.py` 🆕
- 统一 `code/message/data/timestamp` 响应结构（与 `docs/05_接口设计/01_FastAPI接口文档.md` 一致）

#### `app/core/exceptions.py` 🆕
- 错误码与文档对齐：`0/1001/1002/1003/1004/2001/2002/3001/3002/5000`

#### `app/core/dependencies.py` 🆕
- JWT 鉴权依赖 `get_current_user`
- 角色依赖 `require_role("customer"/"service_advisor"/"knowledge_admin")`

---

### 4.2 接口层（`app/api/`）

#### `app/api/http/import_server.py` ✏️ 改写
- 保留 `/upload`、`/status/{task_id}`、`/html`
- 增加业务路由（建议改成「挂载到子应用」或被 `main.py` 统一挂载）：
  - `POST /api/v1/knowledge/documents/upload` → 复用 `invoke_graph`
  - `POST /api/v1/knowledge/documents/parse` → 触发解析（对已上传的 doc）
  - `GET  /api/v1/knowledge/documents/{doc_id}` → 文档详情
  - `GET  /api/v1/knowledge/documents` → 列表/分页
  - `POST /api/v1/knowledge/documents/{doc_id}/publish` → 审核发布
  - `POST /api/v1/knowledge/documents/{doc_id}/offline` → 下线
  - `GET  /api/v1/knowledge/import-tasks/{task_id}` → 进度

#### `app/api/http/query_server.py` ✏️ 改写
- 保留 `/query`、`/stream/{session_id}`、`/history/{session_id}`、`DELETE /history/{session_id}`、`/html`
- 增加业务路由：
  - `POST /api/v1/qa/ask` → 走 query_graph
  - `POST /api/v1/qa/feedback` → `user_feedbacks` 落库
  - `GET  /api/v1/qa/sessions/{session_id}` → 历史

#### `app/api/http/vehicle_server.py` 🆕
- `GET /api/v1/vehicles/{vehicle_id}`
- `GET /api/v1/vehicles/by-vin/{vin}`
- `GET /api/v1/vehicles/{vehicle_id}/maintenance-records`
- `POST /api/v1/vehicles/{vehicle_id}/maintenance-check` → 触发 `domain.maintenance_service`

#### `app/api/http/warranty_server.py` 🆕
- `POST /api/v1/warranty/precheck` → 触发 `domain.warranty_service`，返回 `PreCheckResult` 四档枚举

#### `app/api/http/diagnosis_server.py` 🆕
- `POST /api/v1/diagnosis/run` → 触发 `domain.diagnosis_service`，返回 `risk_level` + `possible_causes` + `suggestion`
- `POST /api/v1/diagnosis/{session_id}/convert-to-repair` → 把诊断会话转报修单

#### `app/api/http/repair_server.py` 🆕
- `POST /api/v1/repair-orders` → 创建报修单
- `GET  /api/v1/repair-orders/{order_id}`
- `PATCH /api/v1/repair-orders/{order_id}/state` → 状态流转
- `POST /api/v1/repair-orders/{order_id}/conclusion` → 提交维修结论

#### `app/api/http/knowledge_admin_server.py` 🆕
- 管理员对 `typical_cases` 审核发布
- `GET/POST/PUT /api/v1/cases`
- `POST /api/v1/cases/{case_id}/publish`

#### `app/api/schemas/*.py`
- `import_schema.py` ✏️：增加 `doc_type`、`vehicle_model`、`component`、`version`、`effective_date`、`expire_date`、`visible_roles`
- `query_schema.py` ✏️：增加 `vehicle_id`、`user_role`、`stream_mode`、`top_k`
- `vehicle_schema.py / repair_schema.py / warranty_schema.py / diagnosis_schema.py / knowledge_schema.py` 🆕：按 `docs/04_数据库设计/01_MongoDB集合设计.md` 定义 Pydantic 模型

---

### 4.3 基础设施层（`app/infra/`）

#### `app/infra/config/providers.py` ✏️ 改写
- 在 `InfraConfig` 中增加：
  - `business: BusinessConfig`（业务库名/角色/超时/阈值）
  - `rag: RagConfig`（chunk_size、top_k、置信度阈值、RRF k）

#### `app/infra/llm/providers.py` ✏️ 改写
- 保留 `chat` / `vision_chat` / `embedding_mode` / `embed_documents` / `reranker_mode`
- 增加：
  - `embed_query(text)` → 单条查询向量（区别于批量入库的 `encode_documents`）
  - `stream_chat(messages)` → LangChain `ChatOpenAI.stream`
  - `json_chat(messages)` → `response_format=json_object`

#### `app/infra/vectorstore/milvus_gateway.py` ✏️ 改写
- 增加 `hybrid_search_with_filter(...)`：传入 `expr`，按 `vehicle_model` / `doc_type` / `state` / `expire_date` 过滤
- 增加 `search_cases(...)`：检索 `kb_cases` 集合（故障现象向量相似）
- 增加 `delete_by_doc_id(doc_id)`：知识更新时清理旧 chunk

#### `app/infra/persistence/*.py`
- `history_repository.py` ✅ 保留
- 其余 `*_repository.py` 🆕：按 `docs/04_数据库设计/01_MongoDB集合设计.md` 中每个集合的字段/索引落库

#### `app/infra/object_stroage/minio_gateway.py` ✅
- 保留；可加 `upload_file(local_path, remote_path)` 上传原始文档

---

### 4.4 公共能力（`app/shared/`）

#### `app/shared/config/business_config.py` 🆕
- 业务库名、各业务集合名、JWT 配置、阈值

#### `app/shared/config/rag_config.py` 🆕
- `RAG_VECTOR_TOPK / RAG_KEYWORD_TOPK / RAG_FINAL_TOPK / RAG_CONFIDENCE_THRESHOLD / RAG_RRF_K`

#### `app/shared/clients/mongo_business_utils.py` 🆕
- 业务库连接单例，封装 `vehicles / repair_orders / warranty_policies / diagnosis_sessions / qa_* / user_feedbacks / typical_cases` 的 CRUD

#### `app/shared/clients/mongo_knowledge_utils.py` 🆕
- 知识库 Mongo 连接单例，封装 `knowledge_documents / knowledge_chunks / import_tasks` 的 CRUD
- 注意：向量仍存 Milvus，这里只存**元数据 + 文本 + chunk_id**；Milvus 中也存 `chunk_id` 关联

#### `app/shared/utils/time_utils.py` 🆕
- 质保期计算、保养周期计算、有效期判断

#### `app/shared/utils/retry_utils.py` 🆕
- 通用重试装饰器（LLM、Milvus、Mongo）

---

### 4.5 业务领域服务（`app/domain/`）

> 这层**不依赖 LangGraph**，是纯业务函数，HTTP 接口和 LangGraph 节点都能复用。

#### `app/domain/diagnosis_service.py` 🆕
- 输入：`vehicle_id / fault_description / fault_codes / fault_images`
- 步骤：
  1. 查询 `warranty_policies`、`maintenance_records`
  2. 走 query_graph 拉取相关知识
  3. 用 `diagnosis.prompt` 让 LLM 输出 `possible_causes / risk_level / suggestion`
  4. 风险等级匹配 `DIAGNOSIS_RISK_HIGH_KEYWORDS` → 升级
  5. 写 `diagnosis_sessions`
- 输出：`{risk_level, possible_causes, suggestion, references, diagnosis_session_id}`

#### `app/domain/warranty_service.py` 🆕
- 严格按 `docs/03_架构设计/01_系统整体架构.md` 第六节 `warranty_precheck` 实现：
  - 维度：时间 / 里程 / 保养 / 免责
  - 枚举：`likely_in_warranty / likely_out_of_warranty / manual_review_required`
- 备注：把 `RAG` 拉到的质保规则作为**辅助材料**给 LLM，但最终结果以**规则引擎**为准；LLM 只负责解释

#### `app/domain/maintenance_service.py` 🆕
- 根据 `vehicles.current_mileage` + `warranty_policies.maintenance_rule` 判断是否到保养节点

#### `app/domain/repair_service.py` 🆕
- 创建/派单/关单/状态机（按 `docs/04_数据库设计/02_状态State枚举设计.md`）

#### `app/domain/case_service.py` 🆕
- 维修结论 → 结构化抽取（故障现象/原因/方案） → 写 `typical_cases` → 管理员审核 → 发布 → 触发 Milvus 入库

---

### 4.6 LangGraph 流程（`app/process/`）

#### 导入流程（`app/process/import_/`）

##### `app/process/import_/agent/state.py` ✏️ 改写
- 增加字段（与 `docs/01_数据导入流程/01_知识导入总流程.md` 对齐）：
  ```python
  doc_id: str
  doc_type: str                       # maintenance_manual / warranty_manual / repair_manual / typical_case / faq
  vehicle_model: str
  component: str
  version: str
  effective_date: str
  expire_date: str | None
  visible_roles: list[str]
  total_chunks: int
  success_chunks: int
  failed_chunks: int
  document_state: str                 # uploaded/parsing/parsed/...（见状态机）
  ```

##### `app/process/import_/agent/main_graph.py` ✏️ 改写
- 在 `node_bge_embedding → node_import_milvus` 之后增加 `node_doc_meta → node_save_knowledge → node_publish`
- 出边接到 `END`

##### `app/process/import_/agent/nodes/` 新增节点
- `node_doc_meta.py`：调用 `rag.import_.doc_meta_service` 抽取元数据
- `node_save_knowledge.py`：调用 `infra.persistence.knowledge_repository` 写 `knowledge_documents / knowledge_chunks / import_tasks`
- `node_publish.py`：默认 `state=pending_review`，等待管理员发布

#### 查询流程（`app/process/query/`）

##### `app/process/query/agent/state.py` ✏️ 改写
- 增加：
  ```python
  user_id: str
  user_role: str
  vehicle_id: str | None
  vehicle_model: str | None
  intent: str                         # maintenance/warranty/fault/case/process/general
  extracted_entities: dict            # 车型/VIN/故障码/里程/部件
  metadata_filter: dict               # 检索期使用的元数据过滤
  vector_chunks: list
  keyword_chunks: list
  structured_chunks: list
  case_chunks: list
  fused_chunks: list
  reranked_chunks: list
  top_score: float
  need_followup: bool
  followup_question: str
  references: list[dict]              # 引用溯源
  ```

##### `app/process/query/agent/main_graph.py` ✏️ 改写
- 流程：
  ```
  node_item_name_confirm
        │ (有 item_names)
        ▼
  node_intent_recognition ── node_entity_extraction ── node_metadata_filter
                                                              │
            ┌───────────────┬───────────────┬───────────────┴──────────────┐
            ▼               ▼               ▼                              ▼
   node_search_embedding  node_keyword_search  node_structured_query    node_case_search
            └───────────────┴───────────────┴──────────────────────────────┘
                                          ▼
                                  node_rrf（融合）
                                          ▼
                                  node_rerank
                                          ▼
                              node_confidence_check
                                  │           │
                          足够（≥阈值）      不足
                                  ▼           ▼
                          node_answer_output  node_followup
                                  ▼
                                node_save_qa
  ```
- 关键：`node_intent_recognition` 和 `node_entity_extraction` 是**新增**的核心节点；融合阶段使用 `RRF` 取代模板里简单的 `WeightRanker`
- 引用：把 `state.references` 一并写入 `qa_references` 集合

##### `app/process/query/agent/nodes/` 新增节点
- `node_intent_recognition.py` 🆕：调用 `intent_recognition.prompt`
- `node_entity_extraction.py` 🆕：调用 `entity_extraction.prompt`，抽 `车型/VIN/故障码/里程/部件`
- `node_keyword_search.py` 🆕：调用 `rag.query.keyword_search_service`（BM25 + 中文分词 jieba）
- `node_structured_query.py` 🆕：调用 `rag.query.structured_query_service`（查 `vehicles/maintenance_records/warranty_policies`）
- `node_case_search.py` 🆕：调用 `rag.query.case_search_service`（Milvus `kb_cases`）
- `node_metadata_filter.py` 🆕：调用 `rag.query.metadata_filter_service`，按 `vehicle_model/doc_type/expire_date/visible_roles` 过滤
- `node_confidence_check.py` 🆕：调用 `rag.query.confidence_service`，Top-1 分数 ≥ 阈值进入生成；否则走追问/无答案/转人工
- `node_save_qa.py` 🆕：把 QA 会话、消息、引用落 Mongo

> 模板中已有的 `node_search_embedding_hyde` 与 `node_web_search_mcp` 保留为「**可选旁路**」，是否启用由 `RAG_ENABLE_HYDE` / `RAG_ENABLE_WEB` 控制。

---

### 4.7 RAG 业务服务（`app/rag/`）

#### 导入侧（`app/rag/import_/`）
- 已有 `entry_service / pdf_parse_service / split_service / item_name_service / embedding_service / index_service / enrich_markdown_images` 保留
- 新增：
  - `doc_meta_service.py` 🆕：用 LLM 抽 `{doc_type, vehicle_model, component, version, effective_date, expire_date, visible_roles}`
  - `knowledge_persist_service.py` 🆕：写 `knowledge_documents / knowledge_chunks / import_tasks`

#### 查询侧（`app/rag/query/`）
- 已有 `answer_service / embedding_search_service / hyde_search_sevice / item_name_confirm_service / rerank_service / rrf_service / web_search_service` 保留
- 新增：
  - `keyword_search_service.py` 🆕：基于 `rank_bm25` + jieba，对 `chunks.content + item_name + keywords` 索引
  - `structured_query_service.py` 🆕：查 `vehicles / maintenance_records / warranty_policies`，结果格式化为 chunk
  - `case_search_service.py` 🆕：Milvus `kb_cases` 向量检索
  - `metadata_filter_service.py` 🆕：在融合前对四路结果做车型/版本/有效期/权限过滤
  - `confidence_service.py` 🆕：低置信度处理（追问 / 无答案 / 转人工），与 `flows/02_RAG检索流程/03_无答案与补充提问流程.md` 对齐
  - `prompt_builder.py` 🆕：组装 `answer_out.prompt` 的 `context/history/item_names/question` 四段
- 改写：
  - `rrf_service.py` ✏️：支持**任意多路**融合（不再只支持 embedding + hyde + web）
  - `answer_service.py` ✏️：调用 `prompt_builder`，并把 `state.references` 写回 state

---

### 4.8 提示词（`app/resources/prompts/`）

| Prompt | 改/新增 | 关键要点 |
|---|---|---|
| `answer_out.prompt` | ✏️ | 强制「只能基于参考内容」「质保说初步预判」「安全风险显式提示」「附引用编号」 |
| `intent_recognition.prompt` | 🆕 | 输出 `maintenance/warranty/fault/case/process/general` |
| `entity_extraction.prompt` | 🆕 | 输出 `{vehicle_model, vin, fault_codes, mileage, component, purchase_date, fault_symptom}` |
| `diagnosis.prompt` | 🆕 | 角色：售后诊断专家；输出 `{risk_level, possible_causes, suggestion}`；不编造 |
| `warranty_precheck.prompt` | 🆕 | 角色：质保规则解释员；输出基于规则的预判 + 解释 |
| `rewritten_query_and_itemnames.prompt` | ✏️ | 改写时融合车型/故障码/里程，让 `rewritten_query` 更结构化 |
| `item_name_recognition.prompt` | ✅ | 保留 |
| `rerank_text_refine.prompt` | ✅ | 保留 |
| `hyde_prompt.prompt` | ✅ | 保留 |
| `image_summary.prompt` | ✅ | 保留 |
| `product_recognition_system.prompt` | ✅ | 保留（按需启用） |

---

### 4.9 工具与脚本（`scripts/`）

#### `scripts/init_milvus_collections.py` 🆕
- 自动创建：
  - `kb_chunks`：`chunk_id`/`file_title`/`content`/`parent_title`/`title`/`part`/`item_name`/`vehicle_model`/`doc_type`/`expire_date`/`state`/`dense_vector(1024)`/`sparse_vector`
  - `kb_cases`：`case_id`/`title`/`fault_symptom`/`vehicle_model`/`tags`/`dense_vector`
  - `kb_entities`/`kb_item_names`：按需
- 索引：`HNSW` + `COSINE`

#### `scripts/init_mongo_collections.py` 🆕
- 按 `docs/04_数据库设计/01_MongoDB集合设计.md` 第三节创建所有索引（`users.phone` 唯一、`vehicles.vin` 唯一、`knowledge_chunks.doc_id` 等）

#### `scripts/seed_demo_data.py` 🆕
- 一键插入演示知识、T5 车型、1 个用户、1 个会话

---

### 4.10 部署（`docker/`）

#### `docker/Dockerfile` 🆕
- 基础镜像 `python:3.11-slim`
- 安装 `libgl1` `libglib2.0-0`（OpenCV 依赖）等
- 复制 `pyproject.toml` + `uv.lock`，用 `uv sync` 安装
- 默认启动 `python -m app.main`

#### `docker/docker-compose.yml` 🆕
- 服务：
  - `milvus`（standalone）
  - `mongo`
  - `minio`
  - `rag-import`
  - `rag-query`
  - `nginx`（可选）

---

## 五、运行步骤

```bash
# 1. 安装依赖（项目已用 uv）
uv sync

# 2. 复制环境变量
cp .env.example .env
# 填入 OPENAI_API_KEY、MINERU_API_TOKEN、Milvus/Mongo/MinIO 地址等

# 3. 启动基础设施
docker compose -f docker/docker-compose.yml up -d milvus mongo minio

# 4. 初始化集合与索引
uv run python scripts/init_milvus_collections.py
uv run python scripts/init_mongo_collections.py
uv run python scripts/seed_demo_data.py

# 5. 启动两个服务（开发模式）
uv run python -m app.api.http.import_server
uv run python -m app.api.http.query_server

# 6. 打开前端原型
# 浏览器：frontend/login.html
```

> 生产环境建议用 `app/main.py` 统一入口，配合 `uvicorn` + `gunicorn` 多 worker。

---

## 六、与现有 docs / flows 的对齐清单

| 设计点 | 文档 | `app/` 对应位置 |
|---|---|---|
| 知识导入总流程 | `flows/01_数据导入流程/01_知识导入总流程.md` | `app/process/import_/agent/main_graph.py` |
| 多路混合检索 | `flows/02_RAG检索流程/01_多路混合检索流程.md` | `app/process/query/agent/main_graph.py` |
| RAG 生成回答 | `flows/02_RAG检索流程/02_RAG生成回答流程.md` | `rag.query.answer_service` + `resources/prompts/answer_out.prompt` |
| 无答案与追问 | `flows/02_RAG检索流程/03_无答案与补充提问流程.md` | `process.query.agent.nodes.node_confidence_check` + `rag.query.confidence_service` |
| MongoDB 集合 | `docs/04_数据库设计/01_MongoDB集合设计.md` | `app/infra/persistence/*_repository.py` + `scripts/init_mongo_collections.py` |
| 状态机 | `docs/04_数据库设计/02_状态State枚举设计.md` | `app/domain/repair_service.py` / `case_service.py` |
| FastAPI 接口 | `docs/05_接口设计/01_FastAPI接口文档.md` | `app/api/http/*_server.py` + `app/api/schemas/*.py` |
| 业务场景 | `flows/03_业务流程/*` | `app/domain/*_service.py` |
| 技术栈 | `docs/03_架构设计/02_技术栈选型说明.md` | `pyproject.toml` + `.env` |

---

## 七、落地优先级（建议执行顺序）

1. **第 1 周**（P0）：`.env` 配置、`main.py` 入口、`lifespan`、`milvus_gateway` 增 `metadata_filter`、`state` 改写、`node_intent_recognition` / `node_entity_extraction` / `node_keyword_search` / `node_structured_query` / `node_case_search` / `node_metadata_filter` / `node_confidence_check` / `node_save_qa`
2. **第 2 周**（P0）：`domain/warranty_service` + `domain/diagnosis_service` + `domain/repair_service`；HTTP 接口 `/api/v1/qa/ask` / `/api/v1/warranty/precheck` / `/api/v1/diagnosis/run` / `/api/v1/repair-orders`
3. **第 3 周**（P1）：知识库管理接口（CRUD/审核发布）；`case_service` 沉淀；Mongo 索引脚本；`init_milvus_collections`
4. **第 4 周**（P1）：Docker 化、压测、引用溯源 UI 联调
5. **第 5 周+**（P2）：HyDE、WebSearch 旁路、多模态图片诊断

---

*文档版本：v1.0 | 更新时间：2026-06-12*
