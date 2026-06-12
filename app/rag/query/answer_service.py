import re
from app.infra.llm.providers import llm_provider
from app.infra.persistence.history_repository import history_repository
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.load_prompt import load_prompt
from app.shared.utils.task_utils import add_done_task,add_running_task,push_to_session
from app.shared.utils.sse_utils import SSEEvent
from app.shared.runtime.logger import logger
import time
import sys



# 拿到state的answer\is_stream 判断有值，strem直接调用 push_to_session( state.get("session_id"),SSEEvent,DELTA逐token返回,data = {“delta”：ch 循环的参数，逐个toke循环参数})
def check_state_had_answer(state):
    """
    检查啊对呀是否有answer
    :param state:
    :return:
    """
    answer = state.get("answer")
    if not answer:
        logger.error(f"没有answer，证明有明确的itemnames正常返回结果")
        return False
    # 我们就给前段返回数据
    # is_stream = True  -> 打字机模型  -> state  (final)
    # is_stream = False ->  answer  -> state
    is_stream = state.get("is_stream",False)
    if is_stream:
        # 流式返回
        for ch in answer:
            push_to_session(
                state.get("session_id"),
                SSEEvent.DELTA,  # 逐token返回，final才是全部返回
                data={"delta": ch}
            )
            # time.sleep(0.06)
    return True


# 校验参数 reranked_docs 、item_names、 rewritten_query
def get_data_and_validate(state):
    """
        获取彬校验
    :param state:
    :return:
    """
    reranker_docs = state.get("reranked_docs",[])
    item_names = state.get("item_names",[])
    rewritten_query = state.get("rewritten_query",[])

    if len(rewritten_query) == 0 or item_names == []:
        logger.error(f"没有reranker，item_name")
        raise ValueError(f"没有reranker，item_name")

    history = history_repository.list_recent(state.get("session_id"),limit=10)
    return reranker_docs,history,item_names,rewritten_query

# 拼接提示词
def load_prompt_text(reranker_docs, history, item_names, rewritten_query):
    # 拼接  context  reranker_docs  [{title,text,type,url[取图片]，score}]
    # 标题：title ， 来源：向量库/web , reranker模型评分：score  \n
    # 内容 xxx
    # \n\n
    #
    context = ""
    for doc in reranker_docs:
        context += f" 标题：{doc.get('title')} 来源 ：{'网络搜索' if doc['type'] == 'web' else '向量库'},'reranker模型评分：'{doc['score']}\n '内容：'{doc['text']}\n\n"

    # history 拼接
    history_text = ""
    final_message_list = [item for item in history if item.get("item_names") and len(item.get('item_names'))>0]

    if final_message_list and len(final_message_list) > 0:
        for index,item in enumerate(final_message_list,start=1):
            history_text += f"序号：{index},你先：{'提问' if item['role'] == 'user' else '回答'},内容：{item['rewritten_query'] if item['role'] == 'user' else item['text']}, 关联主体:{','.join(item['item_names'])}\n"
    else:
        history_text = "没有对话记录!"

    # item_names关联
    item_names_text = ",".join(item_names)

    # 加载提示词模板  第一个是提示词文件，后面都是提示词中的参数
    prompt_text = load_prompt("answer_out",context = context,history = history_text,
                              item_names = item_names_text,question = rewritten_query)
    return prompt_text

# 流式非流式生成
def call_llm_generate(prompt_text, state):
    final_answer = ""
    # 1、获取模型对象
    llm_client = llm_provider.chat()
    # 2、判断是否流式调用
    is_stream = state.get("is_stream",False)
    if is_stream:
        # 一段一段返回
        stream = llm_client.stream(prompt_text)
        for chunk in stream:
            current_content = chunk.content
            push_to_session(
                state.get("session_id"),
                SSEEvent.DELTA,
                data={"delta": current_content}
            )
            final_answer += current_content
    else:
        response = llm_client.invoke(prompt_text)
        final_answer = response.content
    state['answer'] = final_answer

# 提取图片
def extract_image_urls(reranker_docs, state):
    """
    提取图片 url text 转载到列表中
    :param reranker_docs:
    :param state:
    :return:
    """
    # 1、定义一个正则
    # 2、定义一个存储数据的列表
    image_urls:list[str] = []
    # 匹配 markdown 图片正则
    reg = re.compile(r"\!\[.*?\]\((.*?)\)")
    # 3、循环 ->url  /text
    for doc in reranker_docs:
        url = doc.get("url","")
        text =doc.get("text","")
        # 提取url
        if url and url.endswith((".jpg",".jpeg",".png",".gif","svg")):
            image_urls.append(url)
        # 提取text
        for image_url in reg.findall(text):
            if image_url not in image_urls:
                image_urls.append(image_url)
        # 4、给state赋值
        state["image_urls"] = image_urls
        return state

# 保存历史对话
def save_history_message(state):
    history_repository.save_message(
        session_id=state["session_id"],
        role="assistant",
        text=state.get("answer"),
        rewritten_query = state.get("rewritten_query"),
        item_names = state.get("item_names",[]),
        image_urls=state.get("image_urls",[])
    )


def generate_answer(state: QueryGraphState) -> QueryGraphState:
    """
    答案生成服务：
    1. 检查前置答案（如有追问或拒绝回答，直接输出）
    2. 构建 Prompt（用户问题 + 历史对话 + TopK 文档）
    3. 调用 LLM 生成最终答案（支持流式推送）
    4. 从引用文档中提取图片 URL
    5. 写入 MongoDB 历史记录
    6. 回写 answer 和 image_urls
    """
    ""
    # 1、判断是否有结果返回对应状态
    has_answer = check_state_had_answer(state)

    # 2、如果没有结果，才调用模型进行答案生成
    if not has_answer:
        # 3、没有结果，获取并且校验参数
        reranker_docs,history,item_names,rewritten_query = get_data_and_validate(state)

        # 拼接提示词的上下文，加载外部提示词文件
        prompt_text = load_prompt_text(reranker_docs,history,item_names,rewritten_query)

        # 5、调用模型生成文本答案
        call_llm_generate(prompt_text,state)

        # 提取图片列表 -> state[imag_urls] = []
        extract_image_urls(reranker_docs,state)


    #保存历史记录
    save_history_message(state)
    # 返回state
    return state






    # print("---node_answer_output 节点处理开始---")
    # # add_running_task(state["session_id"], sys._getframe().f_code.co_name, state.get("is_stream"))
    #
    # session_id = state["session_id"]
    # # 写死了，检索流程中chunk块给大模型，大模型润色答案后 invoke stream  如果用了否则就是这个
    # is_stream = state.get("is_stream", True)
    # base_answer = state.get("answer") or f"这是关于「{state.get('original_query', '当前问题')}」的测试回答，正在演示打字机流式输出效果"
    # final_text = ""
    #
    # if is_stream:
    #     for ch in base_answer:
    #         final_text += ch
    #         # 增量字符串
    #         push_to_session(session_id, SSEEvent.DELTA, {"delta": ch})
    #         time.sleep(0.06)
    #
    #     push_to_session(session_id, SSEEvent.DELTA, {"delta": "哈哈"})
    #     push_to_session(session_id, SSEEvent.DELTA, {"delta": "哈哈"})
    #     time.sleep(0.66)
    #     logger.info(f"流式输出完成，总长度{len(final_text)}")
    # else:
    #     final_text = base_answer
    #
    # # 存储和答案
    # history_repository.save_message(session_id = state['session_id'],role='assistant',text=final_text,rewritten_query=state['rewritten_query'],item_names=state['item_names'],image_urls=state['image_urls'])
    #
    # # add_done_task(state['session_id'], sys._getframe().f_code.co_name, state.get("is_stream"))
    # print("---node_answer_output 节点处理结束---")
    # # 关键点：return 必须保留 session_id！
    # return {
    #     "session_id": session_id,  # 必须带回去
    #     "answer": "你的回答内容",
    #     "is_stream": state.get("is_stream")
    # }