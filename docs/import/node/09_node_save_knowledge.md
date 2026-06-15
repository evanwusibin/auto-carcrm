# node_09_save_knowledge 知识文档持久化（🆕 新增）

## 模块目的
将知识文档的元信息持久化到MongoDB，支持文档管理和查询。

## 流程图
```
输入：state（含 file_title, item_name, metadata, chunks, md_content）
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 构造文档对象                                                      │
│    knowledge_document = {                                           │
│        "title": file_title,                                         │
│        "item_name": item_name,                                      │
│        "vehicle_model": metadata.get("vehicle_model"),              │
│        "version": metadata.get("version"),                          │
│        "source_type": metadata.get("source_type"),                  │
│        "valid_until": metadata.get("valid_until"),                  │
│        "tags": metadata.get("tags", []),                            │
│        "chunk_count": len(chunks),                                  │
│        "content_length": len(md_content),                           │
│        "status": "draft",                                           │
│        "doc_type": "kb"                                             │
│    }                                                                │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. 保存到MongoDB                                                     │
│    inserted_id = knowledge_repository.save(knowledge_document)      │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. 写入 state                                                       │
│    state["knowledge_doc_id"] = inserted_id                          │
│    return state                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 对应service
knowledge_persist_service.py → persist_knowledge(state)

## 与原项目差异
| 对比项 | 原项目 | 本项目 |
|--------|--------|--------|
| 存储目标 | 只存Milvus | 额外存MongoDB知识文档表 |
| 存储内容 | chunks+向量 | 文档元信息+chunks统计+原始内容 |
| 状态管理 | 无 | draft状态，等待发布 |
| 文档ID | 无 | 生成knowledge_doc_id |

## 踩坑速查
| 坑 | 现象 | 解决 |
|----|------|------|
| MongoDB连接失败 | 插入报错 | 检查MONGO_URL配置 |
| inserted_id类型不对 | ObjectId转str | 用str(inserted_id) |
| metadata为空 | 字段缺失 | 用.get()兜底 |
