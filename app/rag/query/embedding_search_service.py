from app.infra.llm.providers import llm_provider
from app.infra.vectorstore.milvus_gateway import milvus_gateway
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log


@step_log("validate_retrival_state")
def validate_retrival_state(state):
    item_names = state['item_names']
    rewritten_query = state['rewritten_query']
    if not item_names:
        logger.error('item_names not exist')
        raise ValueError('item_names not exist')
    if not rewritten_query:
        logger.error('rewritten_query not exist')
        raise ValueError('rewritten_query not exist')
    return item_names, rewritten_query


# 执行带过滤的混合向量检索
@step_log("search_chunks")
def search_chunks(rewritten_query,item_names):
    embedding_result = llm_provider.embed_documents([rewritten_query])
    dense_vector = embedding_result.get("dense")[0]
    sparse_vector = embedding_result.get("sparse")[0]

    ann_reqs = milvus_gateway.create_requests(
        dense_vector=dense_vector,
        sparse_vector=sparse_vector,
        expr=f"item_name in {item_names}",
        limit=5*2
    )

    # 固定格式
    milvus_result = milvus_gateway.hybrid_search(
        collection_name=milvus_gateway.chunk_collection_name,
        reqs=ann_reqs, # 上一个reqs
        ranker_weights=(0.6,0.4),
        norm_score=True,
        limit = 5,
        output_fields=[
            "chunk_id",
            "item_name",
            "parent_title",
            "part","title",
            "file_title",
            "content"
        ],
    )
    # 结果需要遍历return才行对吧  直接取值搜索出来就是字典结果
    return milvus_result[0] if milvus_result and len(milvus_result)>0 else None



# 结果标准化统一格式化为查询量内部标准结构，需要放在混合查询里面 插入到milvus构造中
@step_log("normalize_retrieved_chunk")
def normalize_retrieved_chunk(chunk:dict):
    final_list_dict = []
    for chunk_dict in chunk:
        entity = chunk_dict.get('entity', {})
        final_list_dict.append({
            "chunk_id": chunk_dict.get("id") or entity.get("chunk_id"),  # 片段ID
            "item_name": entity.get("item_name", ""),  # 归属主体名称
            "title": entity.get("title"),  # 片段标题
            "parent_title": entity.get("parent_title"),  # 父标题/章节
            "part": entity.get("part"),  # 部分标识
            "file_title": entity.get("file_title"),  # 来源文件标题
            "content": entity.get("content", ""),  # 片段文本内容
            "score": chunk_dict.get("distance", 0.0),  # 相似度分数
            "type": "milvus",  # 来源类型（向量库）
            "url": None,
        })
    return final_list_dict

@step_log("search_by_embedding")
def search_by_embedding(state: QueryGraphState) -> QueryGraphState:
    """
    向量检索服务：
    1. 根据改写后的问题和限定的商品范围
    2. 利用 BGEM3 混合检索（稠密+稀疏）技术
    3. 从 Milvus 向量数据库中召回 Top-K 最相关的知识切片
    4. 回写 embedding_chunks

    1. 调用 `llm_provider.embed_documents()` 生成 dense / sparse 向量；
    2. 调用 `build_item_name_expr()` 构造主体过滤表达式；
    3. 调用 `milvus_gateway.create_requests()` 构造混合检索请求；
    4. 调用 `milvus_gateway.hybrid_search()` 检索正文切片；
    5. 调用 `normalize_retrieved_chunk()` 统一整理结果结构；
    6. 返回标准化后的切片列表。

    `node_search_embedding -> search_embedding -> validate_retrieval_state / search_chunks -> build_item_name_expr / normalize_retrieved_chunk
    """
    # 参数获取和校验
    item_names,rewritten_query= validate_retrival_state(state)
    # 进行向量库混合检索
    chunks = search_chunks(rewritten_query=rewritten_query,item_names=item_names)
    # 继续数据格式化处理
    # [dict {id,diatance ,entity :{} }  -> 目标格式 {}]
    final_list_dict = normalize_retrieved_chunk(chunks) if chunks else []
    # 直接返回数据 修改对应node节点即可
    state['embedding_chunks'] = final_list_dict
    return state


