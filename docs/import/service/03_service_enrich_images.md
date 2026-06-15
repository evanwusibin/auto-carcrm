# enrich_markdown_images.py 图片增强服务

## 目的
将MD中的图片上传到MinIO，替换为公网地址，并用Vision模型生成图片描述。

## 核心函数
1. load_markdown_and_image_dir(state) → (md_content, md_path_obj, images_path_obj)
2. scan_images(md_content, image_path_obj) → [(image_name, image_path, (pre, post))]
3. summarize_images(images_context_list, stem) → {image_name: description}
4. upload_images_and_replace(...) → new_md_content
5. back_up_new_md_content(md_content_new, md_path_obj) → new_md_path
6. enrich_markdown_images(state) → state

## 函数签名
```python
def load_markdown_and_image_dir(state: dict) -> tuple
def scan_images(md_content: str, image_path_obj: Path, content_length: int = 100) -> List[tuple]
def summarize_images(images_context_list: list, stem: str) -> Dict[str, str]
def upload_images_and_replace(image_context_list: list, image_summaries_dict: dict, md_content: str, stem: str) -> str
def back_up_new_md_content(md_content_new: str, md_path_obj: Path) -> str
def enrich_markdown_images(state: dict) -> ImportGraphState
```

## 输入输出
- 输入：state（含 md_path, md_content）
- 输出：state（含 md_path(新), md_content(新)）

## 与原项目差异
无变化，直接从原项目复制。

## 对应节点
node_md_img
