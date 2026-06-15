[shared] 共享层：跨模块复用的工具和配置
  - clients/: 客户端工具（milvus_utils/minio_utils/mongo_*_utils）
  - config/: 配置模块（embedding/lm/milvus/minio/mineru/rag/reranker/settings）
  - model/: 模型工具（embedding_utils/lm_utils/reranker_utils/stream_chat_utils）
  - runtime/: 运行时工具（load_prompt/logger）
  - tool/: 下载工具（download_bgem3/download_reranker）
  - utils/: 通用工具（task_utils/sse_utils/time_utils/retry_utils等）
