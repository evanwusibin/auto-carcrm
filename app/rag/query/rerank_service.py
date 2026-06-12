from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from app.infra.llm.providers import llm_provider
from app.shared.runtime.load_prompt import load_prompt

RERANK_MAX_TOPK: int = 10
RERANK_MIN_TOPK: int = 1  # 动态TopK
RERANK_GAP_RATIO: float = 0.25
RERANK_GAP_ABS: float = 0.25
RERANK_MAX_INPUT_TOKENS: int = 512
RERANK_SUMMARY_CHAR_RATIO: float = 1.3
RERANK_MIN_SUMMARY_CHARS: int = 50
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log


@step_log("validate_rerank_inputs")
def validate_rerank_inputs(state:QueryGraphState):
    """
    获取和校验核心参数
    :param state:
    :return:
    """
    rrf_chunks = state.get("rrf_chunks") or []
    rewritten_query = state.get("rewritten_query")
    web_search_docs = state.get("web_search_docs") or []
    # 联网搜索是补充性、依赖网络的可选源,空了不该拖垮整条链路;
    # 只要还有问题且至少一路候选(本地rrf 或 联网)非空就继续重排
    if not rewritten_query or (len(rrf_chunks) == 0 and len(web_search_docs) == 0):
        logger.error(
            f"重排输入为空,业务无法继续: rrf_chunks={len(rrf_chunks)}, "
            f"web_search_docs={len(web_search_docs)}, rewritten_query={bool(rewritten_query)}"
        )
        raise ValueError(f"重排输入为空:本地与联网候选均为空,或缺少rewritten_query")

    return web_search_docs,rewritten_query,rrf_chunks

@step_log("merge_rrf_and_web")
def merge_rrf_and_web(web_search_docs, rrf_chunks):
    """
    合并两个chunk的内容，放到一个新的字典中
    :param web_search_docs:
    :param rrf_chunks:
    :return:
    """
    # 注意字典列表不能直接解包,无需zip  注意字典的解包和append赋值是一起的
    merge_chunks_list = []
    for rrf_chunk in rrf_chunks:
        merge_chunks_list.append({
            "title":rrf_chunk.get("title"),
            "score": rrf_chunk.get("score",0.0),  # [milvus -> rrf的分 |  web -> 0.0] -> reranker
            "text" : rrf_chunk.get("content") or rrf_chunk.get("text") or "",  # milvus正文存在content字段
            "url" : rrf_chunk.get("url"),
            "type" : rrf_chunk.get("type","milvus")  # milvus / web
        })

    for doc in web_search_docs:
        merge_chunks_list.append({
            "title": doc.get("title"),
            "score": 0.0,  # [milvus -> rrf的分 |  web -> 0.0] -> reranker
            "text": doc.get("snippet"),
            "url": doc.get("url"),
            "type": "web"  # milvus / web
        })
    return merge_chunks_list


# 压缩问题函数
@step_log("zip_rewritten_query")
def zip_rewritten_query(rewritten_query:str,answer,limit=RERANK_MAX_INPUT_TOKENS):
    """
    构建问题压缩函数，用于构造打分表超限的情况压缩文本
    :param rewritten_query:
    :param answer:
    :param limit:
    :return:
    """
    llm_client = llm_provider.chat()
    prompt_text = load_prompt("rerank_text_refine",question = rewritten_query ,rewritten_query=rewritten_query,answer=answer,limit = limit)
    message = [
        HumanMessage(content=prompt_text)
    ]
    chains = llm_client | StrOutputParser()
    refine_answer = chains.invoke(message)
    return refine_answer



# 处理问题对   构造 打分问题列表 (压缩过) || data_list (未压缩) || 顺序
@step_log("build_question_pairs")
def build_question_pairs(rewritten_query,merge_chunks_list)->list[list[str]]:
    """
    构造打分表
    :param rewritten_query:
    :param merge_chunks_list:
    :return:
    """
    reranker_model = llm_provider.reranker_mode()
    tokenizer = reranker_model.tokenizer
    query_token = tokenizer.encode(rewritten_query)
    query_token_number = len(query_token)

    reranker_qa_list = []
    for item in merge_chunks_list:
        answer = item.get('text') or ""  # 兜底:正文为空也不能传None给tokenizer
        answer_tokens = tokenizer.encode(str(answer),add_special_tokens=False)
        answer_tokens_number = len(answer_tokens)
        if query_token_number + answer_tokens_number + 4  > RERANK_MAX_INPUT_TOKENS:
            limit = int(max(RERANK_MIN_SUMMARY_CHARS,(RERANK_MAX_INPUT_TOKENS - query_token_number - 4)/RERANK_SUMMARY_CHAR_RATIO))
            #
            answer = zip_rewritten_query(rewritten_query,answer,limit =limit)
        reranker_qa_list.append([rewritten_query,answer])
        # 打分问题列表 (压缩过) || data_list (未压缩) || 顺序
    return reranker_qa_list

@step_log("reranker_score_chunks")
def reranker_score_chunks(reranker_qa_list):
    """
    使用reranker模型打分
    :param reranker_QA_list:
    :return:
    """
    reranker_model = llm_provider.reranker_mode()
    scores_list = reranker_model.compute_score(reranker_qa_list,normalize = True)
    logger.info(f"完成对数据{reranker_qa_list}的打分，分数为{scores_list}")
    return scores_list

@step_log("score_final_chunk")
def score_final_chunk(merge_chunks_list,scores_list):
    """
    从两个字典中取出数据用zip解包两个字典取参数，相互赋值，再继续排序  字典排序用sort+lambda
    :param merge_chunks_list:
    :param scores_list:
    :return:
    """
    for score,qa in zip(scores_list,merge_chunks_list):
        qa['score'] = score

    logger.info(f"没排序前的顺序徐{merge_chunks_list}")
    logger.info("*"*60)
    merge_chunks_list.sort(key=lambda x: x['score'],reverse=True)
    logger.info(f"排序后的{merge_chunks_list}")
    return merge_chunks_list

@step_log("dynamic_topk")
def dynamic_topk(merge_chunks_list):
    """
    动态截取TopK
    :param merge_chunks_list:
    :return:
    """
    global topK
    max_number = RERANK_MAX_TOPK
    min_number = RERANK_MIN_TOPK
    gap_abs = RERANK_GAP_ABS
    gap_ratio = RERANK_GAP_RATIO

    # max_number 大于列表长度
    max_number  = min(max_number,len(merge_chunks_list))

    # 没有断崖默认截取全部，循环目标寻找断崖，不跳出

    # 有可能  min > max
    if max_number > min_number:
        # 其实位置 最大的位置下表 -1  =  max_number - 1 -1 前一个
        for index in range(min_number,max_number-1):
            score_1 = merge_chunks_list[index].get('score',0.0)
            score_2 = merge_chunks_list[index+1].get('score',0.0)
            # 不会出现负分，拉到 0-1
            abs_score = score_1-score_2
            ratio_score = abs_score / (score_1 + 1e-7)

            # 断崖判断
            if abs_score > gap_abs or ratio_score > gap_ratio:
                topK = index + 1
                break
    return merge_chunks_list[:topK]

@step_log("rerank_documents")
def rerank_documents(state: QueryGraphState) -> QueryGraphState:
    """
    #### 步骤分解
    1. 从 `state` 中读取 `rrf_chunks` 和 `web_search_docs`；
    2. 将两路结果整理成统一候选结构；
    3. 读取当前问题 `rewritten_query`；
    4. 使用重排模型自身的 tokenizer 计算“问题 + 文档”总 token 数；
    5. 若候选文本超出 `512` 上下文限制，则先调用大模型做精炼；
    6. 调用重排模型对“问题 - 文档”对计算相关性分数；
    7. 按分数降序排序；
    8. 根据动态 TopK 规则截断最终结果；
    9. 将结果写入 `reranked_docs`。
    **对应 service 作用**: 这一节的重排逻辑拆成了 6 个核心函数：
        1. `validate_rerank_inputs()`：读取重排阶段的两路输入；
        2. `merge_rrf_and_web()`：统一整理本地结果和网页结果结构；
        3. `build_question_pairs()`：使用重排模型 tokenizer 构造问答对，并检查上下文长度；
        4. `summarize_long_rerank_text()`：当文本超长时，先调用大模型精炼后再参与重排；
        5. `score_and_sort_chunks()`：调用重排模型打分并排序；
        6. `dynamic_topk()`：根据分数断崖动态截断结果。

        node_rerank -> rerank_documents -> validate_rerank_inputs ->
        merge_rrf_and_web -> score_and_sort_chunks -> build_question_pairs ->
        summarize_long_rerank_text -> dynamic_topk

        prompt: answer/question/limit
    """
    # 读取重排阶段的两路输入 以及 重写后的问题
    web_search_docs,rewritten_query,rrf_chunks = validate_rerank_inputs(state)
    # 两路读取相同的参数追加到新的列表中组装，用于后续打分使用
    merge_chunks_list = merge_rrf_and_web(web_search_docs,rrf_chunks)
    # 编写模型压缩问题函数rewritten_query


    #================================================
    # 使用重排模型构造问答对，校验上下文长度 构造结构  [[问题，答案]，[问题，答案]] 这里没有分，只有merge_chunk_list才有分
    reranker_qa_list = build_question_pairs(rewritten_query,merge_chunks_list )
    # 打分使用reranker模型进行打分 基于构造好的问题对来打分
    scores_list = reranker_score_chunks(reranker_qa_list)
    #=================================================

    # 5、原始数据继续赋分和排序
    merge_chunks_list = score_final_chunk(merge_chunks_list,scores_list)


    #6、动态TopK算法切块
    merge_chunks_list= dynamic_topk(merge_chunks_list)
    state['reranked_docs'] = merge_chunks_list

    return state





if __name__ == '__main__':
    mock_rrf_chunks = [
        {"chunk_id": "local_1", "text": "喜羊羊最擅长的足球技巧是彩虹过人，曾经一场比赛连过灰太狼七次",
         "title": "喜羊羊足球集锦"},
        {"chunk_id": "local_2", "text": "灰太狼发明了9999种抓羊方法，全部失败，成功率0%", "title": "灰太狼的狼生简历"},
        {"chunk_id": "local_3", "text": "懒羊羊的口头禅是'好困啊'，每天睡眠时长超过20小时，创下羊村吉尼斯纪录",
         "title": "羊村睡眠协会"},
        {"chunk_id": "local_4", "text": "沸羊羊每天举铁500次，但战斗力依然为零，主要作用是给喜羊羊当背景板",
         "title": "健身失败案例"},
        {"chunk_id": "local_5", "text": "美羊羊的蝴蝶结收藏超过300个，是青青草原最大的蝴蝶结囤积症患者",
         "title": "羊村时尚周刊"},
    ]
    mock_web_docs = [
        {"title": "红太狼的平底锅销量报告", "url": "http://pan.com/sales",
         "snippet": "红太狼牌平底锅年销量突破100万口，是灰太狼头上的包的直接供应商"},
        {"title": "羊村年度安全报告", "url": "http://safe.com/report",
         "snippet": "羊村连续15年零伤亡，灰太狼从未成功抓到过一只羊，被评为最安全小区"},
    ]
    mock_state = {
        "session_id": "test_rerank_session",
        "rewritten_query": "灰太狼到底能不能抓住喜羊羊？",
        "rrf_chunks": mock_rrf_chunks,
        "web_search_docs": mock_web_docs,
        "is_stream": False,
    }
    result = rerank_documents(mock_state)
    print(result)