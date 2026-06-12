from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log


@step_log("get_data_and_validate")
def get_data_and_validate(state):
    embedding_chunks = state.get("embedding_chunks")
    hyde_embedding_chunks = state.get("hyde_embedding_chunks")

    if len(embedding_chunks) ==0 and len(hyde_embedding_chunks) == 0:
        logger.error(f"查询数据为空列表无法继续业务，无结果")
        raise ValueError(f"查询数据为空列表无法继续业务，无结果")
    return embedding_chunks, hyde_embedding_chunks


# 2、封装带有权重的结构  把两路打包成 把两路检索结果打包成 (权重, 检索结果) 的元组列表，然后丢给 RRF 算法融合排序。
# 唯一固定的是格式：list[tuple[float, list]]，即 (权重, 该路chunk列表)
@step_log("user_rrf_chunks_list")
def user_rrf_chunks_list(chunks_list:list[tuple[float,dict]], limit, k:int = 60):
    # 带有权重思维的rrf算法计算最终的top limit数量  k是平滑参数  减少排名对结果的过度影响
    # 1、定义两个容器，一是存储chunk_id : 累计分   存储chunk_id :chunk
    score_dict:dict[str,float] = {}
    # 后面的字典是chunk块的内容
    chunk_dict:dict[str,dict] = {}

    # 2、循环每路数据和对应的权重（）（）（）  两路循环两遍
    # 元祖解包（权重，  改路的chunks列表），拆开分别赋值给weight，current_chunks
    for weight,current_chunks in chunks_list:

    # 3、循环当前路计算当前路得分  权重  排名
        for rank ,chunk in enumerate(current_chunks,start=1):  # 元祖解包
            # rank = 排名
            # 公式  1/k+rank
            score_dict[chunk['chunk_id']] = score_dict.get(chunk['chunk_id'],0)+weight*(1/(k+rank))
            # chunk_dict[chunk['chunk_id']] = chunk_dict.get(chunk['chunk_id'],{})
            # 两路相同的chunk 除了score  其他都一样
            # 去重存储 chunk 内容（同一个 chunk_id 只存第一次遇到的）
            # chunk_dict.setdefault(key, value) → key不存在时存入，存在则不变
            chunk_dict.setdefault(chunk['chunk_id'],chunk)

    # 4、处理chunk列表并且继续排序
    # chunk_id 得分  chunk_id   chun _score  milvus
    chunk_list = []
    for chunk_id ,score in score_dict.items():
        chunk = chunk_dict.get(chunk_id)
        chunk['score'] = score
        chunk_list.append(chunk)
    chunk_list.sort(key=lambda chunk: chunk['score'],reverse=True)
    # 5、截取limit数量的chunk列表
    rrf_chunk = chunk_list[:limit]
    return rrf_chunk


@step_log("fuse_by_rrf")
def fuse_by_rrf(state: QueryGraphState) -> QueryGraphState:
    """
    RRF 融合服务：
    1. 合并来自不同检索源的文档列表
    2. 应用 RRF 算法消除分数差异
    3. 给出综合排名最高的文档列表（Top 10）
    4. 回写 rrf_chunks
    """
    # 1、获取数据和校验（向量数据库查询）
    embedding_chunks, hyde_embedding_chunks = get_data_and_validate(state)
    # 2、封装带有权重的结构  把两路打包成 把两路检索结果打包成 (权重, 检索结果) 的元组列表，然后丢给 RRF 算法融合排序。
    # 唯一固定的是格式：list[tuple[float, list]]，即 (权重, 该路chunk列表)
    chunk_list = [
        (1.0,embedding_chunks),
        (1.0,hyde_embedding_chunks),  # 假设性文档 向量检索结果
    ]
    # 3、使用rrf算法计算和解决内容
    rrf_chunks = user_rrf_chunks_list(chunk_list,limit = 5,k = 60)
    logger.info(f"[RRF] rrf_chunks count: {len(rrf_chunks)}")
    state['rrf_chunks'] = rrf_chunks
    return state



