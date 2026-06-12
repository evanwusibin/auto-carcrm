# 定义主图的全局state
import json
# 一共12个属性

# state（TypedDict/Basemodel）

# 1、目标 定义去哪聚state  2、便捷创建state的方法

from typing import TypedDict
import copy
from app.shared.runtime.logger import logger



class ImportGraphState(TypedDict):

    # 任务状态追踪
    task_id :str  # 每次调用流程的表示

    # 文件状态判断
    is_md_read_enabled : bool
    is_pdf_read_enabled : bool

    # 地址路径
    local_file_path : str # 存储要解析的pdf等地址
    local_dir:str  # 存储生成的md文件
    md_path:str # 专门存储md地址
    pdf_path:str
    file_title : str  # 存储文件名称的，无后缀

    # 文本和切块内容
    md_content:str  # 读取md内容用于切片
    item_name:str     # 模型识别的一个文档对应的名称
    chunks:list    # 存储切块的内容
    embeddings_content:list  # 存储带有切块的内容


# 提供下对外快速创建的方法
# 模板
default_state : ImportGraphState = {
    'task_id' : '',
    'is_md_read_enabled' : False,
    'is_pdf_read_enabled' : False,
    'local_file_path' : '',
    'local_dir' : '',
    'md_path' : '',
    'pdf_path' : '',
    'file_title' : '',
    'item_name' : '',
    'chunks' : [],
    'embeddings_content' : [],
    'md_content':""
}

# 提供一个方法，可以返回我们的state，可以根据传入参数继续对象属性修改
# 1、方法（） -> default_state  2、方法（参数） -> default_state(task_id = 传入参数) -> default_state
# 方法task_id = 007,local_file_path = "./md.pdf"
# ** override就是字典解包，能够深拷贝default_state方法里面的内容，避免数据被污染
def create_default_state(**overrides) -> ImportGraphState:
    """
    :param overrides: 传入的参数 key = x  key = x  传入参数转字典，为了方便update方法修改
    :return: 每次返回是基于模板创建的新的字典对象
    """
    # copy [深 浅] 深拷贝
    # 深 copy.deep_copy
    # 浅  copy.copy |  dict（字典） | 字典.copy
    # 更新
    # **字典 {task_id:xx , local_file_path = }  -> 结构 -> task_id = x  ,local_file_path =
    # ** overrides - >  task_id = x ,local_file_path = ->{task_id:xx,local_file_path = }

    copy_state = copy.deepcopy(default_state)
    copy_state.update(overrides)
    return copy_state


def get_default_state() -> ImportGraphState:
    # 方法重载,返回一个新的状态实例，避免全局变量比污染
    return copy.deepcopy(default_state)


if __name__ == '__main__':
    state = create_default_state(task_id = "task_007")
    logger.info(f"测试复制方法: \n {json.dumps(state, ensure_ascii=False,indent=4)}")

    state1 = create_default_state()
    logger.info(f"测试复制方法: \n{json.dumps(state1,ensure_ascii=False,indent=4)}")
