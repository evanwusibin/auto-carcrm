# knowledge_persist_service.py 知识文档持久化服务（🆕 新增）

## 目的
将知识文档的元信息持久化到MongoDB，支持文档管理和查询。

## 核心函数
1. persist_knowledge(state) → state
2. publish_knowledge(state) → state

## 函数签名
```python
def persist_knowledge(state: ImportGraphState) -> ImportGraphState
def publish_knowledge(state: ImportGraphState) -> ImportGraphState
```

## 输入输出
- 输入：state（含 file_title, item_name, metadata, chunks, md_content）
- 输出：state（含 knowledge_doc_id, import_status）

## 与原项目差异
| 对比项 | 原项目 | 本项目 |
|--------|--------|--------|
| 存储目标 | 只存Milvus | 额外存MongoDB知识文档表 |
| 存储内容 | chunks+向量 | 文档元信息+chunks统计+原始内容 |
| 状态管理 | 无 | draft→published |
| 审核机制 | 无 | 支持自动/人工发布 |

## 对应节点
node_save_knowledge, node_publish
