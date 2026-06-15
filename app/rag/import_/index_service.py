from pymilvus import DataType

from app.infra.vectorstore.milvus_gateway import milvus_gateway
from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.config import MILVUS_CHUNK_CONTENT_MAX_LENGTH, MILVUS_DEFAULT_VARCHAR_MAX_LENGTH, MILVUS_VECTOR_DIM
from app.shared.runtime.logger import step_log, logger

# 获取chunks存储到向量数据库
@step_log("validate_chunks_index")
def validate_chunks_index(state:ImportGraphState):
    chunks = state.get("chunks",[])
    if not chunks:
        logger.error(f"无数据{chunks}，请先在chunks中存入数据再说")
        raise ValueError(f"无数据{chunks}，请先在chunks中存入数据再说")
    return chunks


def prepare_chunks_collection():
    milvus_client = milvus_gateway.client
    collection_name = milvus_gateway.chunk_collection_name

    if milvus_client.has_collection(collection_name=collection_name):
        logger.info(f"已经存在集合{collection_name}")
        return
    schema = milvus_client.create_schema(
        auto_id=True,
        enable_dynamic_collection=True,
    )
    schema.add_field(field_name = "chunk_id",datatype = DataType.INT64,is_primary = True)
    schema.add_field(field_name = "file_title",datatype = DataType.VARCHAR,max_length = 512)
    schema.add_field(field_name = "content",datatype = DataType.VARCHAR,max_length = MILVUS_CHUNK_CONTENT_MAX_LENGTH)
    schema.add_field(field_name = "parent_title",datatype = DataType.VARCHAR,max_length = MILVUS_DEFAULT_VARCHAR_MAX_LENGTH)
    schema.add_field(field_name = "title",datatype = DataType.VARCHAR,max_length = MILVUS_DEFAULT_VARCHAR_MAX_LENGTH)
    schema.add_field(field_name = "part",datatype = DataType.INT8)
    schema.add_field(field_name = "item_name",datatype = DataType.VARCHAR,max_length = MILVUS_DEFAULT_VARCHAR_MAX_LENGTH)
    schema.add_field(field_name = "dense_vector",datatype = DataType.FLOAT_VECTOR,dim = MILVUS_VECTOR_DIM)
    schema.add_field(field_name = "sparse_vector",datatype = DataType.SPARSE_FLOAT_VECTOR)

    index_params = milvus_client.prepare_index_params()
    index_params.add_index(
        field_name = "dense_vector",
        index_type = 'HNSW',
        index_name="dense_vector_index",
        metric_type = 'COSINE',
        params = {
            "M":64,
            "efConstruction":100
        }
    )
    index_params.add_index(
        field_name = "sparse_vector",
        index_type = 'SPARSE_INVERTED_INDEX',
        index_name="sparse_vector_index",
        metric_type = 'IP',
        params = {
            'inverted_index_algo':"DAAT_MAXSCORE"
        }
    )
    milvus_client.create_collection(
        collection_name = collection_name,
        schema = schema,
        index_params = index_params
)
    logger.info(f"{collection_name} collection created")


@step_log("remove_old_chunks")
def remove_old_chunks(file_title: str) -> None:
    """
    根据文件名称删除已存在的切片记录
    功能：实现幂等性，确保同一主体重复导入时覆盖旧数据
    :param file_title: 文件名,文件名唯一,主体可能修改
    :return: 无返回值
    """
    # 获取 Milvus 客户端并执行删除操作
    milvus_gateway.client.delete(
        collection_name=milvus_gateway.chunk_collection_name,
        filter=f"file_title=='{file_title}'",
    )


@step_log("insert_chunks")
def insert_chunks(chunks):
    result = milvus_gateway.client.insert(
        collection_name = milvus_gateway.chunk_collection_name,
        data = chunks
    )
    logger.info(f"插入数据成功{milvus_gateway.chunk_collection_name}")
    return result


def index_chunks(state: ImportGraphState) -> ImportGraphState:
    """
    # 目标:将chunks存储到向量数据库
    #1.获取chunks+校验
    # 2. 淮备collection集合 (chunk schema indexs collection)
    #3.插入数据(删除[fie_title]/插入)
    :param state:
    :return:
    入库服务：
    1. 准备集合 schema 和索引
    2. 根据 item_name 删除旧数据
    3. 批量插入新的 chunks
    4. 回写 chunk_id 等入库结果
    """
    chunks = validate_chunks_index(state)
    prepare_chunks_collection()
    remove_old_chunks(state['file_title'])
    insert_result = insert_chunks(chunks)
    ids = insert_result.get("ids", [])
    for i, chunk_id in enumerate(ids):
        if i < len(chunks):
            chunks[i]["chunk_id"] = chunk_id
    return state


