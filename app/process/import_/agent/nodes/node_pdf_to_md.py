"""
节点：文件解析（支持多种格式）
原项目只支持PDF，改造后支持：.pdf / .md / .txt / .docx / .xlsx / .csv
"""
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.pdf_parse_service import parse_file_to_markdown


@node_log("node_pdf_to_md")
def node_pdf_to_md(state: ImportGraphState) -> ImportGraphState:
    """
    节点: 文件解析（支持多种格式）
    原项目只支持PDF，改造后支持：.pdf / .md / .txt / .docx / .xlsx / .csv
    """
    add_running_task(state["task_id"], "node_pdf_to_md")
    state = parse_file_to_markdown(state)
    add_done_task(state["task_id"], "node_pdf_to_md")
    return state
