from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from pymilvus import DataType

from app.infra.vectorstore.milvus_gateway import milvus_gateway
from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.config import ITEM_NAME_CONTEXT_CHUNK_K,ITEM_NAME_CONTEXT_TOTAL_MAX_CHARS
from app.shared.runtime.load_prompt import load_prompt
from app.shared.runtime.logger import logger
from app.infra.llm.providers import llm_provider

#   ##### 4.2 `validate_chunks_and_title`
#  **函数签名**: `validate_chunks_and_title(state: dict) -> tuple[list[dict], str]`
#  **步骤**
#         1. 从 state 中获取 `chunks` 和 `file_title`
#         2. 如果 `chunks` 为空，抛出异常终止流程
#         3. 如果 `file_title` 为空，使用默认值 "default_title" 兜底
#         4. 返回校验后的 `chunks` 和 `file_title`

# 三步走，判断输入路径文件是否为空，校验返回对应路径文件。然后执行函数处理业务
def validate_chunks_and_title(state) -> tuple[list[dict],str]:
    # 1、获取数据chunks和file_title
    chunks = state.get("chunks")
    file_title = state.get("file_title")
    # 非空判断
    if not chunks:
        logger.error(f"chunks内容为空无法继续业务！！")
        raise ValueError(f"chunks内容为空无法继续业务！！")
    if not file_title:
        file_title = chunks[0]["file_title"] or "default_file_title"
    # 返回结果
    return chunks, file_title



def build_document_context(chunks) ->str:
    """
    上下文拼接
    :param chunks:
    :return:
    """
    # 1、截取top k chunks  如果老是截取不到就加大点 config
    top_chunk = chunks[:ITEM_NAME_CONTEXT_CHUNK_K]
    # 2、拼接上下文
    # 切片 1、标题 x 父标题 x 内容 \n
    context = ""
    for index,chunk in enumerate(top_chunk,start=1):
        context += f"切片：{index}标题：{chunk['title']} 父标题{chunk['parent_title']}内容 {chunk['content']}\n"
    # 3、最大的字符长度限制
    final_context = context[:ITEM_NAME_CONTEXT_TOTAL_MAX_CHARS]
    return final_context

# **函数签名**: `recognize_item_name(context: str, file_title: str) -> str`
#
# **步骤**
#
# 1. 获取 LLM 客户端
# 2. 加载系统提示词模板 `product_recognition_system`
# 3. 加载用户提示词模板 `item_name_recognition`，传入 `file_title` 和 `context`
# 4. 构造消息列表（SystemMessage + HumanMessage）
# 5. 调用 LLM 并解析输出
# 6. 如果识别结果为空，使用 `file_title` 兜底
# 7. 返回识别出的主体名称
def recognize_item_name(context, file_title) -> str:
    # 1、获取llm客户端对象  llm providers  .chat
    chat_model = llm_provider.chat()
    # 2、加载外部的提示词
    system_prompt_str = load_prompt("product_recognition_system")
    human_prompt_str = load_prompt(
        "item_name_recognition",
        file_title=file_title,
        context=context,
    )
    # 3、封装成我们提示词格式  HumanMessage  SystemMessage
    message = [
        SystemMessage(content=system_prompt_str),
        HumanMessage(content=human_prompt_str),
    ]
    # 4、组装调用链
    chains = chat_model | StrOutputParser()
    # 5、执行调用链 获取item_name
    item_name = chains.invoke(message)
    logger.info(f"调用模型识别完毕item_name: {item_name}")
    # 6、进行非空判断和兜底复制
    if not item_name:
        item_name = file_title
    # 7、返回item_name
    return item_name

def apply_item_name(chunks, item_name):
    """

    :param chunks:
    :param item_name:
    :return:
    """
    for chunk in chunks:
        chunk['item_name'] = item_name
    logger.info(f"{item_name}")
    return chunks


def embed_item_name(item_name):
    """
    {
        dense: [[],[]]
        sparse:[{index:x},{}]
    }

    # 生成调用llm_provider
    :param item_name:
    :return:
    """
    result = llm_provider.embed_documents([item_name])
    return result['dense'][0],result['sparse'][0]

def prepare_item_name_collection():
    # item_name 存储的集合  一定创建么？？？？？  有就不用创建，没有就创建
    # 先判断有没有索引
    # 1、获取客户端对象

    # 2、判断集合是否存在
    milvus_client = milvus_gateway.client
    # 3、不存在创建集合schema [fiedl]
    if milvus_client.has_collection(collection_name=milvus_gateway.item_collection_name):
        # 存在
        logger.info(f"{milvus_gateway.item_collection_name}已经存在集合")
        return
    #3.1 为空则创建集合
    schema = milvus_client.create_schema(
        auto_id = True,
        enable_dynamic_collection = True,
    )
    # 添加field
    schema.add_field(field_name="pk", datatype=DataType.INT64, is_primary=True)
    schema.add_field(field_name="item_name", datatype=DataType.VARCHAR,max_length=512)
    schema.add_field(field_name="file_title",datatype=DataType.VARCHAR,max_length=512)
    schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=1024)
    schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)
    # 4、创建集合对应index
    # 3、3 准备所以
    # HNSW 类似地图导航  分层图类似地图导航
    # IVF_FLAT  分桶  nlist = 64 找到对应桶 /细化筛选
    # FLAT 效率最低 分的最小
    index_params = milvus_client.prepare_index_params()
    # 3.4 add index
    index_params.add_index(
        # 给那个字段创建索引，字段应该是经常查询的字段
        field_name="dense_vector",
        # 索引的类型，索引就是外部创建一种高效数据类型 [目录]  插叙  内存地址  链接
        index_type="HNSW",
        # 相似度算法 L2[0-2]  COSINE IP[-1,1]
        metric_type="COSINE",
        params={
            "M": 64,
            "efConstruction": 100,

        }
    )
    index_params.add_index(
        field_name="sparse_vector",
        # 稀疏向量 2.6  只有倒排索引
        # 内容 -> 向量相似度
        # doc1 = {1:x,3:x}
        # doc2 = {1：x,4:x}
        # 1位置 = doc1，doc2
        # 3位置 = doc1
        # 4位置 = doc2
        # 搜索的系数想来个 {1：k} -> doc1,doc2
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="IP",
        params={"inverted_index_algo": "DAAT_MAXSCORE"}
    )
    # 5、创建集合 集合名字、schema、index
    milvus_client.create_collection(
        collection_name=milvus_gateway.item_collection_name,
        schema=schema,
        index_params=index_params
    )
    logger.info(f"{milvus_client.collection_name}完成初始化第一次")


def upsert_item_name(item_name, file_title, dense_vector, sparse_vector):
    """
    显示出  再插入 幂等性
    :param itemname:
    :param file_title:
    :param dense_vector:
    :param sparse_vector:
    :return:
    """
    milvus_client = milvus_gateway.client
    # 1、先根据file_title删除
    milvus_client.delete(
        collection_name=milvus_gateway.item_collection_name,
        filter=f"file_title == '{file_title}'"
    )
    # 2、插入数据即可
    milvus_client.insert(
        collection_name=milvus_gateway.item_collection_name,
        data=[{
            "item_name": item_name,
            "file_title": file_title,
            "dense_vector": dense_vector,
            "sparse_vector": sparse_vector
        }]
    )

def recognize_and_index_item_name(state: ImportGraphState) -> ImportGraphState:
    """
    主体识别服务：
    1. 基于 chunks 构造上下文
    2. 调用 LLM 识别 item_name
    3. 将 item_name 回填到 state 和 chunks
    4. 同步写入主体名称索引
    """
    # 1、进行参数校验
    chunks,file_title = validate_chunks_and_title(state)
    # 2、进行上下文拼接  content title  chunk  parent_title
    context = build_document_context(chunks)
    # 3、
    item_name = recognize_item_name(context, file_title)

    # 修改所有chunks的item_name
    apply_item_name(chunks,item_name)

    # 将item_name输出结果继续向量化
    dense_vector,sparse_vector = embed_item_name(item_name)

    # 7、准备itemname的集合信息
    # 8、更新state信息
    prepare_item_name_collection()

    upsert_item_name(item_name,file_title,dense_vector,sparse_vector)

    state['item_name'] = item_name
    state['chunks'] = chunks

    return state