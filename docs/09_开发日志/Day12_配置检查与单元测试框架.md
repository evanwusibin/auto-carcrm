# Day 12 开发日志：配置检查 + 前端替换 + 单元测试框架

> 日期：2026-06-12
> 阶段：项目初始化与基础搭建

---

## 一、今日完成内容

### 1.1 配置文件检查与修正

| 文件 | 修改内容 | 说明 |
|------|----------|------|
| `.env` | LLM模型改为 mimo-v2.5-pro | 使用小米自研模型 |
| `.env` | VL模型改为 mimo-v2-omni | 支持图片视觉理解 |
| `.env` | 新增 RAG 配置 | chunk_size、topk、置信度阈值等 |
| `pyproject.toml` | 项目名改为 auto-carcrm | 与老师要求一致 |
| `app/shared/config/rag_config.py` | 新增 enable_hyde / enable_web | 可选旁路配置 |

### 1.2 前端页面替换

| 操作 | 说明 |
|------|------|
| 备份旧页面 | `app/resources/html/backup/chat.html.bak` |
| 备份旧页面 | `app/resources/html/backup/import.html.bak` |
| 替换 chat.html | 从 `frontend/search.html` 复制 |
| 替换 import.html | 从 `frontend/import.html` 复制 |

### 1.3 单元测试框架搭建

| 文件 | 说明 |
|------|------|
| `tests/__init__.py` | 测试包初始化 |
| `tests/conftest.py` | pytest 配置，提供 fixture |
| `tests/test_import_graph.py` | 导入流程测试（7个用例） |
| `tests/test_query_graph.py` | 查询流程测试（7个用例） |

### 1.4 测试结果

```
============================= 14 passed in 7.34s ==============================

tests/test_import_graph.py::TestNodeEntry::test_node_entry_with_pdf PASSED
tests/test_import_graph.py::TestNodeEntry::test_node_entry_with_md PASSED
tests/test_import_graph.py::TestNodePdfToMd::test_pdf_conversion PASSED
tests/test_import_graph.py::TestNodeDocumentSplit::test_document_split PASSED
tests/test_import_graph.py::TestNodeDocumentSplit::test_empty_content PASSED
tests/test_import_graph.py::TestNodeBgeEmbedding::test_embedding_generation PASSED
tests/test_import_graph.py::TestNodeImportMilvus::test_import_to_milvus PASSED
tests/test_query_graph.py::TestNodeItemNameConfirm::test_item_name_confirm_with_valid_input PASSED
tests/test_query_graph.py::TestNodeItemNameConfirm::test_item_name_confirm_with_no_match PASSED
tests/test_query_graph.py::TestNodeSearchEmbedding::test_search_embedding PASSED
tests/test_query_graph.py::TestNodeRrf::test_rrf_fusion PASSED
tests/test_query_graph.py::TestNodeRerank::test_rerank PASSED
tests/test_query_graph.py::TestNodeAnswerOutput::test_answer_generation PASSED
tests/test_query_graph.py::TestNodeAnswerOutput::test_answer_with_images PASSED
```

---

## 二、技术知识点

### 2.1 pytest fixture

```python
@pytest.fixture
def sample_state():
    """示例状态数据，用于测试"""
    return {
        "task_id": "test-001",
        "session_id": "sess-test-001",
    }
```

**作用**：提供测试数据，避免重复代码。

### 2.2 unittest.mock.patch

```python
with patch("app.process.import_.agent.nodes.node_entry.resolve_input_file") as mock_resolve:
    mock_resolve.return_value = {...}
    result = node_entry(state)
```

**作用**：Mock 外部依赖，隔离测试环境。

### 2.3 测试命名规范

```python
def test_node_entry_with_pdf(self):
    """测试PDF文件识别"""
```

**规范**：`test_` 开头 + 被测函数 + 测试场景

---

## 三、遇到的问题与解决

### 问题1：loguru 模块找不到

**原因**：pytest 使用了系统 Python，而不是项目虚拟环境

**解决**：使用 `uv run pytest` 运行测试

### 问题2：测试数据缺少 is_stream 字段

**原因**：实际代码中 `add_running_task` 需要 `is_stream` 参数

**解决**：在测试数据中添加 `"is_stream": False`

---

## 四、下一步计划

```
第1天：实现 node_intent_recognition（意图识别）+ 测试
第2天：实现 node_entity_extraction（实体抽取）+ 测试
第3天：实现 keyword_search_service（BM25检索）+ 测试
第4天：改写 state.py（增加新字段）+ 测试
第5天：改写 main_graph.py（串联新节点）+ 测试
```

---

*文档版本：v1.0 | 更新时间：2026-06-12*
