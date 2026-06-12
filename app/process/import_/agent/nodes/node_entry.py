# sse web socket
"""
应用主包 / 导入流程兼容层 / 图编排子模块 / 节点适配层中的 node_entry 模块，负责承载对应场景的具体实现逻辑。
"""
import sys
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.import_.agent.state import ImportGraphState, create_default_state
from app.rag.import_.entry_service import resolve_input_file

"""
  节点作用: 接收传入的文件地址(local_file_path)识别文件类型,修改对应的state
  入参:  local_file_path / task_id
  出参:  is_md_read_enabled is_pdf_read_enabled  md_path  pdf_path  file_title 
  步骤:
       0. 日志动作  @node_log + 任务列表记录 (进行中,已完成)
       1. 获取state中数据 local_file_path task_id
       2. 进行文件校验 local_file_path 是否为空
       3. 根据地址判断文件类型,修改对应的state参数即可
       4. 识别文件地址对应的文件名称
       5. 返回结果和状态 
       
    @node_log("node_entry")->方法进入和方法执行完毕 以及异常的日志
    节点方法(state :ImportGraphState)
    打印开始的日志
    1. add_running_task(state["task_id"], "node_entry")3.add_done_task(state["task_id"], "node_entry")
    2.state = resolve_input_file(state)调用节点业务函数[节点+ 业务的关联]
    开营结束的日志
    return state
    为啥add_running_task / add_done_task:记录节点的完成状态，存储到对应task_id的列表中(此时:还是英文)为啥要传入task_id: 因为我们有很多客户端，为每个客户端存储一个对应的列表，最终存储到dict[task_id，[]]
    
    为啥add_running_task /add_done_task:记录节点的完成状态，存储到对应task_id的列表中为啥要传入task_id: 因为我们有很多客户端，为每个客户端存储一个对应的列表，最终存储到dict
    节点名称是固定的么:是的，因为后续 get的时候使用列表推到式 将英文 转成对应的中文，定义的时候
    
    节点方法(state :ImportGraphState)
    @node_Log("节点名") ->方法进入和方法执行完毕 以及异常的日志
    打印开始的日志
    1. add_running_task(state["task_id"], "node_entry")
    2.state = resolve_input_file(state) 调用节点业务函数 [节点 + 业务的关联]
    3. add_done_task(state["task_id"], "node_entry")
    开营结束的日志
    return state
       
       
       
"""
@node_log("node_entry")
def node_entry(state: ImportGraphState) -> ImportGraphState:
    """
    节点: 入口节点 (node_entry)
    为什么叫这个名字: 作为图的 Entry Point，负责接收外部输入并决定流程走向。
    """
    add_running_task(state["task_id"], "node_entry")
    # 这里仅负责识别文件类型和补齐基础状态，不承担重业务逻辑。
    state = resolve_input_file(state)
    add_done_task(state["task_id"], "node_entry")
    return state

# @node_log("node_etry")
# def node_entry(state:ImportGraphState) -> ImportGraphState:
#     """
#     节点：入口节点（node_entry）
#     作为图的Entry point 负责接受外部输入并决定流程走向
#     :param state:
#     :return:
#     """
#     add_running_task(state["tsak_id"],"node_entry")
#     state = resolve_input_file(state)
#     add_done_task(state["task_id"],"node_entry")
#     return state



if __name__ == '__main__':

    # 单元测试：覆盖不支持类型、MD、PDF三种场景
    logger.info("===== 开始node_entry节点单元测试 =====")

    # 测试1: 不支持的TXT文件
    test_state1 = create_default_state(
        task_id="test_task_001",
        local_file_path="联想海豚用户手册.txt"
    )
    node_entry(test_state1)

    logger.info(f"测试1结果: {test_state1}")

    # 测试2: MD文件
    test_state2 = create_default_state(
        task_id="test_task_002",
        local_file_path="小米用户手册.md"
    )
    node_entry(test_state2)

    logger.info(f"测试2结果: {test_state2}")

    # 测试3: PDF文件
    test_state3 = create_default_state(
        task_id="test_task_003",
        local_file_path="万用表的使用.pdf"
    )
    node_entry(test_state3)

    logger.info("===== 结束node_entry节点单元测试 =====")
