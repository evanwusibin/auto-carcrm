# embedding_service.py 向量化服务

## 目的
将文本切块转换为向量，支持后续的语义检索。

## 核心函数
1. require_chunks(state) → chunks
2. embed_chunks(chunks) → chunks_with_vectors
3. generate_chunk_embeddings(state) → state

## 函数签名
```python
def require_chunks(state: dict) -> list
def embed_chunks(chunks: list) -> list
def generate_chunk_embeddings(state: dict) -> ImportGraphState
```

## 输入输出
- 输入：state（含 chunks）
- 输出：state（含 chunks(加了向量)）

## 与原项目差异
无变化，直接从原项目复制。

## 对应节点
node_bge_embedding
