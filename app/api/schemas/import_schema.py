# 上传文件的响应数据类型
from pydantic import BaseModel

# 上传文件响应的数据类
class UploadSchema(BaseModel):
    code:int = 200
    message:str
    task_ids:list[str]


# 查询任务状态的数据类型
class TaskStatusSchema(BaseModel):
    code:int = 200
    task_id:str   # 当前查询的task_id
    status:str    # 当前task_id  对应整体和宏观状态  processing 处理中 completed 已完成  field 失败
    done_list:list[str]   # 当前task_id 已完成的任务列表，有多个
    running_list:list[str]   # 当前task_id正在运行的任务列表，同一时刻
