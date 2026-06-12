"""
导入入口服务模块，负责识别输入文件类型并初始化导入状态。
"""
from pathlib import Path
from app.shared.runtime.logger import logger, step_log
from app.process.import_.agent.state import ImportGraphState


@step_log("resolve_input_file")
def resolve_input_file(state: ImportGraphState) -> ImportGraphState:
    """
    识别导入文件类型并初始化后续节点所需的状态字段。
    入口识别服务：
    1. 校验 local_file_path
    2. 识别文件类型（PDF / Markdown）
    3. 回写 is_pdf_read_enabled / is_md_read_enabled
    4. 回写 pdf_path / md_path / file_title
    Args:
        state: 导入图当前状态，需至少包含 `local_file_path`。

    Returns:
        dict: 补充了文件路径、文件标题及开关字段后的最新状态。  字典取值可以用[""],也可以用get("")
    """
    # 1. 获取state local_file_path 属性  state['key'] ->  state.get(key)
    local_file_path = state.get("local_file_path")
    # 2. 进行local_file_path验证,为空 ->  打印异常日志 抛出异常
    if not local_file_path:
        # logger.warning("节点:node_entry,获取文件输入地址,发现地址为空!直接跳转到END节点")
        logger.error(f"节点:node_entry,获取文件输入地址,发现地址为空!直接跳转到END节点,直接抛出异常")
        raise ValueError("节点:node_entry,获取文件输入地址,发现地址为空!直接跳转到END节点，无法继续进行")
        return state

    local_file_path = state.get("local_file_path")

    # 3. 判断是md  is_md_read_enabled = True  md_path =  local_file_path
    # 识别 Markdown / PDF 两类主流程输入，并打开对应处理开关。
    if local_file_path.endswith(".md"):
        state["md_path"] = local_file_path
        state["is_md_read_enabled"] = True
        # state["is_pdf_read_enabled"] = False
    # 4. 判断是pdf is_pdf_read_enabled = True  pdf_path =  local_file_path
    elif local_file_path.endswith(".pdf"):
        state["pdf_path"] = local_file_path
        state["is_pdf_read_enabled"] = True
        # state["is_md_read_enabled"] = False
    # 5. else啥也不是  打印日志 warring  直接返回 state
    else:
        logger.warning(f"虽然local_file_path有值{local_file_path},不是md或者pdf类型,所以无法识别,直接跳转到END节点!")
        return state


    # 6、处理local_file_path -> file_title  -> state
    # lcoal_fike_path  ->  str  ->  路径  ->
    # Path  ->   .name  =  xx.md   .stem 去掉后缀   = xx.md   .parent  .parents[1]
    # read_text()
    # write_text()
    # read_bytes()
    # write_bytes()
    # 6. 处理local_file_path -> file_title -> state
    state["file_title"] = Path(local_file_path).stem
    # 7、 返回state  处理完毕
    return state



