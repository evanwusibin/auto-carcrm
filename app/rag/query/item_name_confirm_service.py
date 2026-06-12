from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from app.infra.llm.providers import llm_provider
from app.infra.persistence.history_repository import history_repository
from app.infra.vectorstore.milvus_gateway import milvus_gateway
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.load_prompt import load_prompt
from app.shared.runtime.logger import logger


# 1、获取参数和校验  state   original_query   session_id
def get_data_and_validate(state:QueryGraphState)->tuple[str,str]:
    """
        进行必要参数校验!
           主要获取原始问题 original_query 和 session_id
        :param state:
        :return: 校验后结果
        """
    original_query = state.get("original_query")
    session_id = state.get("session_id")
    if not original_query:
        logger.info("业务核心参数original_query或者session_id为空,业务无法继续进行!")
        raise ValueError("业务核心参数original_query或者session_id为空,业务无法继续进行!")
    if not session_id:
        logger.info("业务核心参数original_query或者session_id为空,业务无法继续进行!")
        raise ValueError("业务核心参数original_query或者session_id为空,业务无法继续进行!")
    return session_id,original_query

# 2、获取历史聊天记录 输入：session_id, limit=10     输出：list[dict] 历史消息
def get_history_message(session_id,limit:int=10)->list[dict]:
    """
    获取历史聊天记录! 倒序 limit=10
      只获取有效的聊天记录! item_names有数据为判断依据
    :param session_id: 筛选条件
    :param limit: 筛选数量
    :return: 有效数据集合
    """
    history_message_list = history_repository.list_recent(session_id=session_id,limit=limit)
    logger.info(f"查询历史记录数量：{len(history_message_list)}")
    # 有效校验
    final_history_list = [item for item in history_message_list if  item.get("item_names") and len(item['item_names']) > 0]
    logger.info(f"校验后历史记录数量：{len(final_history_list)}")
    return final_history_list






# 3、拼接历史聊天记录 输入：有效的历史消息列表 输出：str history_text
def build_history_context_text(history_message_list:list[dict])-> str:
    """
     构建当前会话对应的上下文!
     历史记录已经完成了校验!
     约定格式: 序号,类型: 提问 / 回答 ,内容: text/rewritten_query , 关联主体: 1,2,3 \n
    :param history_message_list:
    :return:
    """
    history_text = ""
    # item -》 聊天记录 _id  role   text  rewritten_query  ts  item_names  image_urls
    for index,item in enumerate(history_message_list,start=1):
        history_text += f"需要：{index},你先：{'提问' if item['role']== 'user' else '回答'},内容：{item['rewritten_query'] if item['role'] == 'user' else item['text']}, 关联主体:{','.join(item['item_names'])}\n"
    logger.info(f"最终拼接历史记录上下文：{history_text}")
    return history_text




# 4、调用大模型进行问题重写与识别item_name  输入：history_text, original_query  输出：dict{item_names: [], rewritten_query: ""}
def call_llm_deal_data(history_text:str,original_query:str)->dict:
    """
    调用模型进行问题重写和item_name识别
    注意: 返回的是json格式! 需要使用JsonOutputParser进行处理
    :param history_text: 历史记录
    :param original_query: 原始问题
    :return: dict
    """
    # 方法: 加载模型   构建提示词  调用链   执行获取结果  校验结果非空 结果赋值 return
    # 1、加载模型 json model
    json_llm_client = llm_provider.chat(json_mode=True)
    # 2、构建提示词
    prompt_text = load_prompt("rewritten_query_and_itemnames",history_text = history_text,query = original_query)
    messages = [
        HumanMessage(
            content=prompt_text,
        )
    ]
    # 3、构建调用链
    chain = json_llm_client | JsonOutputParser()
    # 4、执行获取结果
    # { item_names :[] ,rewritten_query: 重写问题}
    result_dict = chain.invoke(messages)
    # 5、校验结果
    if "item_names" not in result_dict:
        result_dict["item_names"] = []
    if "rewritten_query" not in result_dict:
        result_dict["rewritten_query"] = original_query
    # 6、返回结果
    return result_dict


# 5、通过milvus混合查询item_name  输入：item_names（模型识别的列表） 输出：{item_name: [{item_name:库里, score:0.8}, ...]}  前提：item_names不为空
def query_item_name_milvus(item_names:list[str])->dict[str,list[dict]]:
    """
    从向量数据库进行item_name查询和结果处理! 注意是混合查询!!
    :param item_names: 模型识别,但是没有通过milvus确认的数据
    :return: 返回milvus中关联的高分数据! 但是先不截取
    """
    # 1、定义前置存储容器
    milvus_result_dict = {}
    # 2、循环处理每个item_names(模型返回)
    for item_name in item_names:
        # 3、每个item_name 向量化 ，获取对应的稠密向量和稀疏向量
        embedding_result = llm_provider.embed_documents([item_name])
        dense_vector = embedding_result['dense'][0]
        sparse_vector = embedding_result['sparse'][0]
        # 4、组装对应的annSearchRequest对象列表
        ann_request_list = milvus_gateway.create_requests(dense_vector,sparse_vector,limit=10)
        # 5、继续混合数据检索，获取结果
        milvus_search_result = milvus_gateway.hybrid_search(
            collection_name=milvus_gateway.item_collection_name,
            reqs = ann_request_list,
            ranker_weights=(0.4,0.6),
            norm_score=True,
            limit=5
        )
        # 6、单个条结果解析
        real_result = milvus_search_result[0]
        if not real_result or len(real_result)==0:
            # 没有查到数据
            logger.warning(f"模型提供的{item_name}没有检索到对应的数据库，吊钩本地")
             # 没有查到数据
            continue


        # 变形  [{iten_name,score},{}]
        current_item_name_list = [{"item_name":item_dict.get('entity').get('item_name'),"score":item_dict.get('distance',0)} for item_dict in real_result]
        milvus_result_dict[item_name] = current_item_name_list

        """
             item_name -> llm 

             {item_name: [{item_name:数据库中的name,score:distance}....5]}

             [
               [ -> real 
                 {
                    id: x,
                    distance: 0.6,
                    entity:{
                       item_name: 数据库中的name
                    }
                 },

                 {
                    id: x,
                    distance: 0.6,
                    entity:{
                       item_name: 数据库中的name
                    }
                 }
                 5个..... 20 ->  权重排名器  -> 5 
               ]
             ]
             """
    return milvus_result_dict
        # milvus_search_result [[{id:1,distance:0.8,entity:{item_name:向量查询}}]]
        # 7. 添加到对应的dict容器中
        # 8. 返回结果
        #  {item_n ame: [{item_name:数据库中的name,score:distance}....5]}


# 6、最后确认和明确item_name  输入的是llm输出的items列表 输入：{item_name: [{item_name:库里, score:0.8}, ...]}    输出：{确认列表: [], 可选列表: []}
def select_item_names(milvus_result_dic):
    """
      根据现有的数据,确定可选或者确认列表!
         {
           item_name :  [{item_name:数据库,score:0.72},{...}],  确认 1  可选 2
           item_name :  [{item_name:数据库,score:0.72},{...}],  确认 1  可选 2
           item_name :  [{item_name:数据库,score:0.72},{...}]   确认 1  可选 2
         }
    :param milvus_result_dict:
    :return:
    """
    # 1 定义两个列表
    confirm_item_name_list = []
    options_item_name_list = []

    # 2、 循环处理每一个item_name 对应的列表
    for item_name ,milvus_list in milvus_result_dic.items():
        # 没必要
        milvus_list.sort(key = lambda x:x['score'],reverse=True)
        # 筛选列表 高分[>0.7]  可选 [0.6 - 0.7]
        high_item_names = [item['item_name'] for item in milvus_list if item['score']>=0.6]
        md_item_names = [item['item_name'] for item in milvus_list if 0.5<item['score']<0.6]

        # 添加确认列表 1个
        if len(high_item_names)>0:
            confirm_item_name_list.append(high_item_names[0])
            continue
        # 没哟可以确认的可选的
        if len(md_item_names)>0:
            # 注意  可能是多个，所以要继承   只能extend，平铺，用append就会列表套列表
            options_item_name_list.extend(md_item_names[:2])
            continue
    return {
        "confirmed_item_name_list":confirm_item_name_list,
        "options_item_name_list":options_item_name_list
    }



# 7、返回最终的状态状态修改  确认列表和可选列表   重写的问题  输入：确认列表, 可选列表, rewritten_query   输出：state
def change_state_status(state:QueryGraphState,item_name_dict,rewritten_query:str):
    """
     修改state状态
        确认列表有值
            item_names = 确认列表
            rewritten_query = rewritten_query
            return
        可选列表有值
            rewritten_query = rewritten_query
            answer = 客客气气...
            return
        都没有值
            rewritten_query = rewritten_query
            answer = 客客气气...
            return
    :param state:
    :param item_name_dict:
    :param rewritten_query:
    :return:
    """
    confirm_item_name_list = item_name_dict.get('confirmed_item_name_list',[])
    options_item_name_list = item_name_dict.get('options_item_name_list',[])

    if confirm_item_name_list and len(confirm_item_name_list)>0:
        # 有确认的
        state['item_names'] = confirm_item_name_list
        state['rewritten_query'] = rewritten_query
        return


    if options_item_name_list and len(options_item_name_list)>0:
        state['rewritten_query'] = rewritten_query
        answer = f"你是要询问：{','.join(options_item_name_list)} 这些内容嘛？  请确认！！！"
        state['answer'] =  answer
        return state

    state['rewritten_query'] = rewritten_query
    answer = f"完全没有识别到你说的主体，请确认有没有上传过这个主体的文件信息，再提问！！！"
    state['answer'] = answer


# 8、保存聊天记录
def save_history_message(state):
    """
    保存聊天记录
    :param state:
    :return:
    """
    history_repository.save_message(
        session_id=state['session_id'],
        role="user",
        text = state.get('original_query'),
        rewritten_query=state['rewritten_query'],
        item_names=state.get('item_names',[]),
    )

# 9、主函数入口
def confirm_item_name(state: QueryGraphState) -> QueryGraphState:
    """
    意图确认服务：
    1. 结合历史对话提取商品名
    2. 将模糊问题改写为完整独立的精准问题
    3. 在 Milvus 向量库中进行混合搜索
    4. 根据评分高低自动对齐标准型号，或生成反问让用户手动确认
    5. 同步历史记录到 MongoDB
    """
    # 假装存储数据
    # history_repository.save_message(session_id = state['session_id'],role = "user",text = state["original_query"],rewritten_query = state["rewritten_query"],item_names = state["item_names"],image_urls = state["image_urls"])
    # 1、获取参数和校验（state） => original_query   session_id
    session_id,original_query = get_data_and_validate(state)
    # 2. 获取当前会话对应历史聊天记录(10条) [注意:只获取有效数据]
    history_message_list = get_history_message(session_id, 10)
    # 3. 构建上下文,注意角色问题 user -> rewritten_query  assistant -> text
    history_text = build_history_context_text(history_message_list)
    # 4. 使用模型进行item_names和问题重写
    # 参数 history_text和original_query  响应: 字典 {item_names:[],rewritten_query:''}
    # 方法: 加载模型   构建提示词  调用链   执行获取结果  校验结果非空 结果赋值 return
    result_dict = call_llm_deal_data(history_text,original_query)

    item_name_dict = {}
    # 5. 进行校验,如果没有item_names无需调用向量查询
    if len(result_dict['item_names']) > 0:
        # 6.进行item_names内部识别到模型名称的向量化查询
        milvus_result_dict:dict[str,list[dict]] = query_item_name_milvus(result_dict['item_names'])
        # 7. 获取确认和可选地列表  dict{确认:[0.7 + ] 可选:[ 0.6 - 0.7 ]}
        item_name_dict = select_item_names(milvus_result_dict)
    else:
        # 兜底：LLM未识别时，用原始query直接搜Milvus
        logger.info(f"[兜底] LLM未识别item_name，用original_query搜索: {original_query}")
        milvus_result_dict = query_item_name_milvus([original_query])
        item_name_dict = select_item_names(milvus_result_dict)
    # 最后返回 确认列表, 可选列表, rewritten_query   修改state状态
    change_state_status(state,item_name_dict,result_dict['rewritten_query'])
    # 保存本地问题的聊天记录
    save_history_message(state)
    return state