# 模块01：entry_service.py（导入入口服务）

> 文档编号：DOC-IMPORT-01 | 版本：v1.0 | 更新时间：2026-06-12
> 对应文件：`app/rag/import_/entry_service.py`

---

## 一、模块目的

**一句话**：识别用户上传的文件是PDF还是MD，打开对应的处理开关，为后续节点路由提供依据。

**类比**：就像快递分拣员，看包裹上的标签（.pdf/.md），然后放到对应的传送带上。

---

## 二、流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│  entry_service.py 流程                                               │
└─────────────────────────────────────────────────────────────────────┘

输入：state（包含 local_file_path）
         │
         ▼
┌─────────────────────┐
│ 1. 获取 local_file_path │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐     ┌─────────────────────┐
│ 2. 校验是否为空      │────→│ 为空：抛出异常        │
└─────────────────────┘     └─────────────────────┘
         │ 非空
         ▼
┌─────────────────────┐
│ 3. 判断文件后缀      │
└─────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ .md   │ │ .pdf  │
└───────┘ └───────┘
    │         │
    ▼         ▼
┌─────────────────────┐
│ 4. 设置路由开关      │
│    is_md_read_enabled │
│    is_pdf_read_enabled│
│    md_path / pdf_path │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 5. 提取文件标题      │
│    file_title = stem │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 6. 返回 state        │
└─────────────────────┘
```

---

## 三、与老师项目的差异

| 维度 | 老师项目 | 本项目 | 说明 |
|------|----------|--------|------|
| **代码逻辑** | 完全相同 | 完全相同 | 直接复用，无需改造 |
| **State字段** | 基础字段 | 新增元数据字段 | 增加了 doc_type/vehicle_model/component 等 |
| **文件类型** | 只支持 .md/.pdf | 只支持 .md/.pdf | 后续可扩展 .docx/.txt |
| **日志装饰器** | @step_log | @step_log | 完全相同 |

---

## 四、主要改造点

### 4.1 State新增字段（已完成）

```python
# 老师项目的 ImportGraphState
task_id, is_md_read_enabled, is_pdf_read_enabled, local_file_path, 
local_dir, md_path, pdf_path, file_title, md_content, item_name, chunks

# 本项目新增的字段
doc_id, doc_type, vehicle_model, component, version, 
effective_date, expire_date, visible_roles, document_state
```

**为什么加这些字段**：
- `doc_type`：区分文档类型（维修手册/质保手册/FAQ），用于后续意图识别和检索过滤
- `vehicle_model`：车型信息，用于元数据过滤（用户问"T5保养"时只检索T5相关文档）
- `component`：部件信息，用于精准检索
- `visible_roles`：权限控制，不同角色看到不同文档

### 4.2 后续可扩展（TODO）

```python
# 当前只支持 .md/.pdf，后续可扩展
if local_file_path.endswith(".docx"):
    # 调用 python-docx 解析
    pass
elif local_file_path.endswith(".txt"):
    # 直接读取
    pass
```

---

## 五、核心知识点

### 5.1 Path.stem 用法

```python
from pathlib import Path

path = Path("/data/documents/华为T5维修手册.pdf")
print(path.stem)    # "华为T5维修手册"（去掉后缀）
print(path.suffix)  # ".pdf"（只要后缀）
print(path.name)    # "华为T5维修手册.pdf"（文件名）
print(path.parent)  # "/data/documents"（父目录）
```

### 5.2 state.get() vs state[]

```python
# 推荐用 get()，不会报错
local_file_path = state.get("local_file_path")  # 不存在返回 None

# 不推荐用 []，会报 KeyError
local_file_path = state["local_file_path"]  # 不存在会崩溃
```

### 5.3 条件边路由

```python
# main_graph.py 中的条件边
def after_entry_node(state):
    if state.get('is_md_read_enabled'):
        return "node_md_img"
    elif state.get('is_pdf_read_enabled'):
        return "node_pdf_to_md"
    else:
        return END
```

---

## 六、踩坑速查

| 坑 | 现象 | 解决 |
|----|------|------|
| `Path.stem` 拼错 | 提取不出文件名 | `Path(local_file_path).stem` |
| 忘记设置开关 | 后续节点路由失败 | 确保设置了 `is_md_read_enabled` 或 `is_pdf_read_enabled` |
| 后缀判断顺序 | `.md.pdf` 误判 | 先判断 `.md` 再判断 `.pdf` |

---

## 七、测试用例

```python
if __name__ == '__main__':
    from app.process.import_.agent.state import create_default_state
    
    # 测试1：MD文件
    state1 = create_default_state(
        task_id="test_001",
        local_file_path="D:/data/华为T5维修手册.md"
    )
    result1 = resolve_input_file(state1)
    print(f"MD测试: {result1}")
    
    # 测试2：PDF文件
    state2 = create_default_state(
        task_id="test_002", 
        local_file_path="D:/data/华为T5维修手册.pdf"
    )
    result2 = resolve_input_file(state2)
    print(f"PDF测试: {result2}")
    
    # 测试3：不支持的文件类型
    state3 = create_default_state(
        task_id="test_003",
        local_file_path="D:/data/test.txt"
    )
    result3 = resolve_input_file(state3)
    print(f"TXT测试: {result3}")
```

---

*文档版本：v1.0 | 更新时间：2026-06-12*
