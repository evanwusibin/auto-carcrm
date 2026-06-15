# node_10_publish 审核发布（🆕 新增）

## 模块目的
将文档状态从draft改为published，完成导入流程。

## 流程图
```
输入：state（含 knowledge_doc_id, is_auto_publish）
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 获取参数                                                          │
│    knowledge_doc_id = state.get("knowledge_doc_id")                 │
│    is_auto_publish = state.get("is_auto_publish", True)             │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. 更新文档状态                                                      │
│    if is_auto_publish:                                              │
│        knowledge_repository.update_status(                          │
│            knowledge_doc_id,                                         │
│            status="published"                                       │
│        )                                                            │
│    else:                                                            │
│        # 保持draft状态，等待人工审核                                  │
│        pass                                                         │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. 写入 state                                                       │
│    state["import_status"] = "completed"                             │
│    return state                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 对应service
knowledge_persist_service.py → publish_knowledge(state)

## 与原项目差异
| 对比项 | 原项目 | 本项目 |
|--------|--------|--------|
| 导入完成 | 直接结束 | 有明确的发布节点 |
| 状态管理 | 无 | draft→published |
| 审核机制 | 无 | 支持自动/人工发布 |

## 踩坑速查
| 坑 | 现象 | 解决 |
|----|------|------|
| knowledge_doc_id为空 | 跳过发布 | 检查persist_knowledge是否执行 |
| MongoDB更新失败 | 状态没改 | 检查update_status实现 |
| 重复发布 | 状态覆盖 | 先检查当前状态 |
