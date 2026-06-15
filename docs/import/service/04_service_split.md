# split_service.py 文档切块服务

## 目的
将长文档按标题切分成小块，保证语义完整性。

## 核心函数
1. load_markdown_content(state) → (md_content, file_title, md_path_obj)
2. split_by_titles(md_content, file_title) → chunks
3. refine_chunks(chunks, max_len, min_len) → final_chunks
4. backup_chunks_json(final_chunks, md_path_obj)
5. split_document(state) → state

## 函数签名
```python
def load_markdown_content(state: dict) -> tuple
def split_by_titles(md_content: str, file_title: str) -> list
def refine_chunks(chunks: list, max_len: int = 1000, min_len: int = 600) -> list
def backup_chunks_json(chunks: list, md_path_obj: Path)
def split_document(state: dict) -> ImportGraphState
```

## 输入输出
- 输入：state（含 md_path, md_content, file_title）
- 输出：state（含 chunks）

## 与原项目差异
无变化，直接从原项目复制。

## 对应节点
node_document_split
