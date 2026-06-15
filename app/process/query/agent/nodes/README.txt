[process/query/agent/nodes] 查询流程节点（调度层）
  已有节点：
    - node_item_name_confirm.py: 意图确认+主体识别
    - node_search_embedding.py: 向量检索
    - node_search_embedding_hyde.py: HyDE检索
    - node_web_search_mcp.py: 网络搜索
    - node_rrf.py: RRF融合
    - node_rerank.py: 重排序
    - node_answer_output.py: 答案生成
  新增节点：
    - node_intent_recognition.py: 意图识别
    - node_entity_extraction.py: 实体抽取
    - node_keyword_search.py: BM25关键词检索
    - node_structured_query.py: 结构化查询
    - node_case_search.py: 案例检索
    - node_metadata_filter.py: 元数据过滤
    - node_confidence_check.py: 置信度判断
    - node_save_qa.py: QA落库
