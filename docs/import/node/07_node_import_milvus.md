# node_07_import_milvus 入库

## 模块目的
将带向量的切块存入Milvus向量数据库。

## 流程图
```
输入：chunks, item_name
  ↓
1. 校验chunks非空
2. 创建集合（如不存在）
3. 删除旧数据（幂等）
4. 批量插入
  ↓
输出：无（数据存入数据库）
```

## 对应service
index_service.py → index_chunks(state)

## 与原项目差异
无变化，直接从原项目复制。

## 踩坑速查
| 坑 | 现象 | 解决 |
|----|------|------|
| `auto_id=True` | 主键自增，不用手动指定 | Milvus自动生成chunk_id |
| `enable_dynamic_field=True` | 允许插入未定义的字段 | 灵活扩展 |
| `score`字段不存在 | output_fields写了score报错 | score是搜索结果自动返回的 |
