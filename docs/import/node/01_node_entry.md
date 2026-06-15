# node_01_entry 入口节点

## 模块目的
根据文件后缀决定走MD还是PDF分支。

## 流程图
```
输入：local_file_path
  ↓
1. 校验文件路径非空
2. 提取文件后缀（.md / .pdf）
3. 提取文件名（不含后缀）
4. 设置路由开关
  ↓
输出：is_md/pdf_enabled, file_title, local_dir
```

## 对应service
entry_service.py → resolve_input_file(state)

## 与原项目差异
无变化，直接从原项目复制。

## 踩坑速查
| 坑 | 现象 | 解决 |
|----|------|------|
| Path().suffix | 获取后缀带点号 | `.md` 不是 `md` |
| Path().stem | 获取文件名不含后缀 | `test.pdf` → `test` |
