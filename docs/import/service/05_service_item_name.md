# item_name_service.py 主体识别服务

## 目的
识别文档的核心主体（如产品名称），并将其关联到每个切块。

## 核心函数
1. validate_chunks_and_title(state) → (chunks, file_title)
2. build_document_context(chunks) → context
3. recognize_item_name(context, file_title) → item_name
4. apply_item_name(state) → state
5. embed_item_name(item_name) → (dense, sparse)
6. upsert_item_name(item_name, file_title, dense, sparse)
7. recognize_and_index_item_name(state) → state

## 函数签名
```python
def validate_chunks_and_title(state: dict) -> tuple
def build_document_context(chunks: list) -> str
def recognize_item_name(context: str, file_title: str) -> str
def apply_item_name(state: dict) -> dict
def embed_item_name(item_name: str) -> tuple
def upsert_item_name(item_name: str, file_title: str, dense: list, sparse: dict)
def recognize_and_index_item_name(state: dict) -> ImportGraphState
```

## 输入输出
- 输入：state（含 chunks, file_title）
- 输出：state（含 item_name, chunks(已回填)）

## 与原项目差异
无变化，直接从原项目复制。

## 对应节点
node_item_name_recognition
