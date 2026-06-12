from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.config import EMBEDDING_BATCH_SIZE
from app.shared.runtime.logger import logger, step_log
from app.infra.llm.providers import llm_provider


def require_chunks(state)->list[dict]:
    # 1、获取chunks
    chunks = state.get("chunks")
    # 2、非空校验
    if not chunks or len(chunks) ==0:
        logger.error(f"chunks数据被置空，无法继续业务")
        raise ValueError(f"chunks数据被置空，无法继续业务")
    return chunks

    # 批量生成想来那个 预设值 5个一批
    # embedding


def embed_chunks(chunks,*,step:int = EMBEDDING_BATCH_SIZE):
    # 1、分批循环获取chunks内容
    final_chunks = []
    for index  in range(0,len(chunks),step):
        # index 0  5  10   切片
        # 获取盗窃案批次
        step_chunks = chunks[index:index+step]
        # 组装生成向量的字符串列表
        step_vector_list = []
        for current_chunk in step_chunks:
            # 匹配规则 item_name + content
            step_vector_list.append(
                f"主体名：{current_chunk['item_name']}，内容：{current_chunk['content']}"
            )
        # 5、批量生成向量
        result = llm_provider.embed_documents(step_vector_list)
        """
            result = {
                    "dense"：[[],[],[]]
                    "spsrse":[{},{}]
                }
        """
        # 循环获取向量创建一个新的chunks添加到final_chunks
        for index,chunk in enumerate(step_chunks):
            # 浅拷贝不拷贝内容  item_name  content   向量 = []  第一层
            chunk_new = chunk.copy()
            chunk_new['dense_vector'] = result['dense'][index]
            chunk_new['sparse_vector'] = result['sparse'][index]
            final_chunks.append(chunk_new)
    return final_chunks


@step_log("generate_chunk_embeddings")
def generate_chunk_embeddings(state: ImportGraphState) -> ImportGraphState:
    """
    向量化服务：
    1. 读取 chunks
    2. 生成 dense_vector / sparse_vector
    3. 将向量结果补充回 chunks
    """
    chunks = require_chunks(state)
    # 带有向量
    final_chunks = embed_chunks(chunks)
    state['chunks'] = final_chunks
    return state