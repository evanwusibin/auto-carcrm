# pdf_parse_service.py PDF解析服务

## 目的
将PDF文件解析为Markdown格式。

## 核心函数
1. validate_pdf_path(state) → (pdf_path_obj, local_dir_obj)
2. upload_pdf_and_poll(pdf_path_obj) → zip_url
3. download_and_extract_markdown(zip_url, local_dir, stem) → md_path_obj
4. parse_pdf_to_markdown(state) → state

## 函数签名
```python
def validate_pdf_path(state: dict) -> tuple
def upload_pdf_and_poll(pdf_path_obj: Path) -> str
def download_and_extract_markdown(zip_url: str, local_dir: Path, stem: str) -> Path
def parse_pdf_to_markdown(state: dict) -> ImportGraphState
```

## 输入输出
- 输入：state（含 pdf_path, local_dir）
- 输出：state（含 md_path, md_content）

## 与原项目差异
无变化，直接从原项目复制。

## 对应节点
node_pdf_to_md
