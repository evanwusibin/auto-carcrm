# node_06_bge_embedding 向量化

## 模块目的
将文本切块转换为向量，支持后续的语义检索。

## 流程图
```
输入：chunks
  ↓
1. 校验chunks非空
2. 分批向量化（BGE-M3）
3. 绑定dense_vector和sparse_vector
  ↓
输出：chunks(加了向量)
```

## 对应service
embedding_service.py → generate_chunk_embeddings(state)

## 与原项目差异
无变化，直接从原项目复制。

## 踩坑速查
| 坑 | 现象 | 解决 |
|----|------|------|
| `chunk.copy()`没用 | 直接改chunk污染上游 | 用浅拷贝 |
| 单批次失败导致整体失败 | 一个chunk报错全挂 | try-except跳过继续 |
| 显存溢出 | 批次太大 | 分批处理（EMBEDDING_BATCH_SIZE） |
