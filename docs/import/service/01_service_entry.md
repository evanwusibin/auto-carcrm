# entry_service.py 入口服务

## 目的
根据文件后缀决定走MD还是PDF分支。

## 核心函数
resolve_input_file(state)

## 函数签名
```python
def resolve_input_file(state: dict) -> ImportGraphState
```

## 输入输出
- 输入：state（含 local_file_path）
- 输出：state（含 is_md/pdf_enabled, file_title, local_dir）

## 与原项目差异
无变化，直接从原项目复制。

## 对应节点
node_entry
