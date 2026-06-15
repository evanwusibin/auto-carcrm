# 非 Service 层文件完善记录

> 更新时间：2026-06-13

本次完善范围：所有「不含 service」的骨架/空文件，包括配置、工具、基础设施、领域服务层。

---

## 一、配置与依赖

### 1.1 `.env`
- 模型地址已切换为 `https://token-plan-cn.xiaomimimo.com/v1`
- API Key 已更新为你的自定义 key
- 默认模型改为 `mimo-v2.5-pro`，VL 模型改为 `mimo-v2-omni`

### 1.2 `pyproject.toml`
- 新增依赖：`rank-bm25>=0.2.2`（BM25 关键词检索）、`jieba>=0.42.1`（中文分词）
- 运行 `uv sync` 安装新依赖

---

## 二、空文件补全（3 个）

### 2.1 `shared/utils/retry_utils.py`
**功能**：通用重试装饰器
- `retry()` — 同步重试，支持指数退避（delay × backoff）
- `async_retry()` — 异步重试，用于 LLM/Milvus 等异步调用
- 用法：`@retry(max_retries=3, delay=1.0, exceptions=(ConnectionError,))`

### 2.2 `shared/utils/time_utils.py`
**功能**：日期/时间计算工具
- `parse_date()` — 支持多种日期格式解析（`2024-03-01`、`2024/03/01`、`2024年03月01日`）
- `days_between()` — 计算两个日期之间的天数
- `is_within_period()` — 判断是否在某个期限内（年/月）
- `calculate_warranty_expire()` — 计算质保到期日
- `is_within_mileage()` — 判断里程是否在质保范围内
- `get_next_maintenance_date()` — 计算下次保养日期
- `format_datetime()` — ISO 格式化

### 2.3 `shared/model/stream_chat_utils.py`
**功能**：LangChain 流式输出封装
- `stream_chat_response()` — 异步生成器，逐 token 返回 LLM 输出
- `stream_chat_with_context()` — 带上下文的流式问答

---

## 三、基础设施层完善（2 个）

### 3.1 `core/lifespan.py`
**改动**：取消注释，恢复启动预热逻辑
- MongoDB 业务库连接（`get_business_db`）
- MongoDB 知识库连接（`get_knowledge_db`）
- MinIO 客户端初始化（`get_minio_client`）
- Embedding 模型预热（`get_bge_m3_ef`）
- Reranker 模型预热（`get_reranker_model`）
- 每步都有 try/except 保护，单个失败不影响其他模块

### 3.2 `infra/document_parse/mineru_gateway.py`
**改动**：从只暴露配置属性 → 完整的 PDF 解析网关
- `upload_pdf(file_path)` — 上传 PDF 到 MinerU API，返回 task_id
- `poll_task(task_id)` — 轮询任务状态，支持超时和失败检测
- `download_result(download_url, save_dir)` — 下载 zip 并解压
- `extract_markdown(file_path, save_dir)` — 一键完成：上传 → 轮询 → 下载 → 返回 .md 路径
- 全局单例 `mineru_gateway`

---

## 四、业务持久化层完善（6 个 Repository）

所有 Repository 遵循统一模式：`@property col` 获取集合 → CRUD 方法 → 全局单例。

### 4.1 `infra/persistence/vehicle_repository.py`
- `find_by_id` / `find_by_vin` / `find_by_owner` / `find_all`
- `save` / `update` / `update_mileage`
- 集合：`vehicles`

### 4.2 `infra/persistence/repair_repository.py`
- `find_by_id` / `find_by_user` / `find_by_vehicle` / `find_by_state`
- `save` — 自动设置 `state=submitted`、`state_history=[]`
- `update_state` — 状态流转，自动记录 `state_history`
- `update` — 通用更新
- 集合：`repair_orders`

### 4.3 `infra/persistence/warranty_repository.py`
- `find_by_id` / `find_by_model_and_component` / `find_by_model` / `find_all_active`
- `save` / `update`
- 集合：`warranty_policies`

### 4.4 `infra/persistence/diagnosis_repository.py`
- `find_by_id` / `find_by_user` / `find_by_vehicle`
- `save` — 自动设置 `state=diagnosing`
- `update_result` / `update_state` / `mark_converted`（转报修单）
- 集合：`diagnosis_sessions`

### 4.5 `infra/persistence/qa_repository.py`
- `find_session` / `save_session` — qa_sessions 集合
- `find_messages` / `save_message` — qa_messages 集合
- `save_references` / `find_references` — qa_references 集合
- `save_feedback` — user_feedbacks 集合

### 4.6 `infra/persistence/case_repository.py`
- `find_by_id` / `find_published` / `find_by_model_and_symptom` / `find_pending_review`
- `save` — 自动设置 `state=pending_review`
- `publish` / `reject` / `update`
- 集合：`typical_cases`

---

## 五、领域服务层完善（5 个 Domain Service）

### 5.1 `domain/repair_service.py` — 报修单管理
**核心逻辑**：
- `create()` — 创建报修单，自动从车辆档案填充 VIN/车型/里程
- `get()` / `list_by_user()`
- `update_state()` — 状态机校验，合法流转：`submitted→accepted→assigned→inspecting→repairing→completed→confirmed`
- `submit_conclusion()` — 提交维修结论
- `customer_confirm()` — 客户确认+评价

### 5.2 `domain/warranty_service.py` — 质保预判
**核心逻辑**：
- `precheck()` — 四维判断：
  1. 时间维度：购车日期 + 质保年限 → 是否超期
  2. 里程维度：当前里程 vs 质保里程上限
  3. 查 `warranty_policies` 集合获取规则
  4. 返回三档结果：`likely_in_warranty` / `likely_out_of_warranty` / `manual_review_required`
- 免责声明：始终附带"初步预判"提示

### 5.3 `domain/maintenance_service.py` — 保养判断
**核心逻辑**：
- `check()` — 判断是否需要保养：
  1. 查最近一条保养记录
  2. 对比当前里程 vs `next_maintenance_mileage`
  3. 对比当前日期 vs `next_maintenance_date`
  4. 距上次保养超过 9000km 给出提醒
  5. 返回 `maintenance_due` / `normal` / `no_records`
- `get_records()` / `add_record()`

### 5.4 `domain/diagnosis_service.py` — 智能诊断
**核心逻辑**：
- `run()` — 完整诊断流程：
  1. 查车辆档案获取车型/里程
  2. 风险评估 `_assess_risk()`：关键词匹配 + 故障码匹配 → `high/medium/low`
  3. 原因分析 `_analyze_causes()`：基于故障现象和故障码推断可能原因
  4. 建议生成 `_generate_suggestion()`：按风险等级给出不同建议
  5. 写 `diagnosis_sessions` 集合
- 高风险关键词来自 `.env` 的 `DIAGNOSIS_RISK_HIGH_KEYWORDS`
- `get_session()` / `list_by_user()`

### 5.5 `domain/case_service.py` — 案例沉淀
**核心逻辑**：
- `submit()` — 提交案例，可关联报修单（自动填充车型/故障描述/故障码）
- `get()` / `list_published()` / `list_pending_review()`
- `publish()` — 管理员审核发布
- `reject()` — 管理员驳回
- `search_by_symptom()` — 按故障现象关键词搜索

---

## 六、改动后的文件状态汇总

| 层级 | 文件 | 改前状态 | 改后状态 |
|------|------|---------|---------|
| 工具层 | `retry_utils.py` | ❌ 空文件 | ✅ 已实现 |
| 工具层 | `time_utils.py` | ❌ 空文件 | ✅ 已实现 |
| 工具层 | `stream_chat_utils.py` | ❌ 空文件 | ✅ 已实现 |
| 核心层 | `lifespan.py` | ⚠️ 骨架 | ✅ 已实现 |
| 基础设施 | `mineru_gateway.py` | ⚠️ 骨架 | ✅ 已实现 |
| 持久化 | `vehicle_repository.py` | ⚠️ 骨架 | ✅ 已实现 |
| 持久化 | `repair_repository.py` | ⚠️ 骨架 | ✅ 已实现 |
| 持久化 | `warranty_repository.py` | ⚠️ 骨架 | ✅ 已实现 |
| 持久化 | `diagnosis_repository.py` | ⚠️ 骨架 | ✅ 已实现 |
| 持久化 | `qa_repository.py` | ⚠️ 骨架 | ✅ 已实现 |
| 持久化 | `case_repository.py` | ⚠️ 骨架 | ✅ 已实现 |
| 领域层 | `repair_service.py` | ⚠️ 骨架 | ✅ 已实现 |
| 领域层 | `warranty_service.py` | ⚠️ 骨架 | ✅ 已实现 |
| 领域层 | `maintenance_service.py` | ⚠️ 骨架 | ✅ 已实现 |
| 领域层 | `diagnosis_service.py` | ⚠️ 骨架 | ✅ 已实现 |
| 领域层 | `case_service.py` | ⚠️ 骨架 | ✅ 已实现 |

---

## 七、下一步待完善

仍为空文件的查询流程服务（需要你来写或继续让我写）：

| 文件 | 功能 | 优先级 |
|------|------|--------|
| `rag/query/keyword_search_service.py` | BM25 关键词检索 | P0 |
| `rag/query/structured_query_service.py` | 车辆档案/保养/质保规则查询 | P0 |
| `rag/query/case_search_service.py` | 典型案例向量检索 | P0 |
| `rag/query/metadata_filter_service.py` | 元数据过滤 | P0 |
| `rag/query/confidence_service.py` | 置信度判断+追问 | P0 |
| `rag/query/prompt_builder.py` | Prompt 组装 | P0 |

导入流程中 2 个 `raise NotImplementedError` 的文件：

| 文件 | 功能 | 优先级 |
|------|------|--------|
| `rag/import_/pdf_parse_service.py` | MinerU API 调用 | P1 |
| `rag/import_/enrich_markdown_images.py` | 图片增强 | P1 |
