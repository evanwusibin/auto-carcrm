[infra] 基础设施层：封装外部依赖（LLM/Milvus/MinIO/MongoDB/MinerU）
  - config/: 配置管理（providers.py统一入口）
  - document_parse/: 文档解析（MinerU网关）
  - llm/: 大模型网关（providers.py提供chat/vision_chat/embed_documents/reranker）
  - object_storage/: 对象存储（MinIO网关）
  - persistence/: 数据持久化（history/knowledge/vehicle/case等Repository）
  - vectorstore/: 向量数据库（Milvus网关，提供create_requests/hybrid_search）
