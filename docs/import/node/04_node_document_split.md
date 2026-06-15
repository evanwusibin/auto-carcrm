# node_04_document_split 文档切块

## 模块目的
将长文档按标题切分成小块，保证语义完整性，便于后续向量化。

## 流程图
```
输入：md_path, md_content, file_title
  ↓
1. 加载MD内容
2. 按标题粗切（split_by_titles）
3. 长切短合（refine_chunks）
4. 备份JSON
  ↓
输出：chunks: list[dict]
```

## 对应service
split_service.py → split_document(state)

## 与原项目差异
无变化，直接从原项目复制。

## 踩坑速查
| 坑 | 现象 | 解决 |
|----|------|------|
| `{1:6}` vs `{1,6}` | 正则量词用逗号不是冒号 | `{1,6}`表示1到6次 |
| `is_code_block = not is_code_block` | 去掉not就只能进不能出 | 用not翻转状态 |
| `return`缩进进了for | 只处理第一个就返回 | return在循环外 |
| `extend(字典)` | 字典被拆成key | 字典用append |
| `md_content.replace()`没接住 | 返回新串没赋值 | `md_content = md_content.replace(...)` |
