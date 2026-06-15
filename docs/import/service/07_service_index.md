# index_service.py 入库服务

## 目的
将带向量的切块存入Milvus向量数据库。

## 核心函数
1. require_chunks(state) → chunks
2. prepare_chunks_collection()
3. remove_old_chunks(item_name)
4. insert_chunks(chunks)
5. index_chunks(state) → state

## 函数签名
```python
def require_chunks(state: dict) -> list
def prepare_chunks_collection()
def remove_old_chunks(item_name: str)
def insert_chunks(chunks: list)
def index_chunks(state: dict) -> ImportGraphState
```

## 输入输出
- 输入：state（含 chunks, item_name）
- 输出：state（无新增字段，数据存入数据库）

## 与原项目差异
无变化，直接从原项目复制。

## 对应节点
node_import_milvus
