# doc_meta_service.py 元数据抽取服务（🆕 新增）

## 目的
从文档标题和MD内容中自动抽取元数据（车型/版本/有效期/文档类型）。

## 核心函数
1. extract_vehicle_model(title, content) → vehicle_model
2. extract_version(title, content) → version
3. extract_dates(content) → (effective_date, expiry_date)
4. extract_doc_type(title, content) → doc_type
5. extract_doc_meta(state) → state

## 函数签名
```python
def extract_vehicle_model(title: str, content: str) -> str
def extract_version(title: str, content: str) -> str
def extract_dates(content: str) -> tuple
def extract_doc_type(title: str, content: str) -> str
def extract_doc_meta(state: ImportGraphState) -> ImportGraphState
```

## 输入输出
- 输入：state（含 file_title, md_content）
- 输出：state（含 vehicle_model, doc_version, effective_date, expiry_date, doc_type）

## 与原项目差异
| 对比项 | 原项目 | 本项目 |
|--------|--------|--------|
| 元数据 | 只有item_name | 增加车型/版本/来源/有效期/标签 |
| LLM调用 | 无 | 可选调用LLM提取 |
| 存储位置 | 无 | 存入state["metadata"] |

## 对应节点
node_doc_meta
