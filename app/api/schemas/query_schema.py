from typing import Any

from pydantic import BaseModel

# 用户提的问题
class QueryRequestParam(BaseModel):
    query: str
    session_id: str
    is_stream:bool = False

# 流式响应后端返回的内容 yield  异步任务
# 流式请求：  用户请求 --- 返回session_id  后端逐个token返回  通过SSE 逐token推送 event：delta\n\n  event:final
class QueryStreamResponse(BaseModel):
    message: str
    session_id: str


# 非流式响应后端返回的内容同步任务
# 用户请求   全部生成完成   一次性返回answer
class QueryNotStreamResponse(BaseModel):
    message: str
    session_id: str
    answer:str
    done_list:list
    image_urls:list


# 清空历史记录响应结构
class HistoryCleanResponse(BaseModel):
    message: str
    deleted_count: str

# 查询历史聊天记录结构
class HistoryItemResponse(BaseModel):
    id:str
    session_id: str
    role:str
    text:str
    rewritten_query:str = ""
    item_names:list = []
    image_urls:list = []
    ts:Any

class HistoryResponse(BaseModel):
    session_id: str
    items:list[HistoryItemResponse]
