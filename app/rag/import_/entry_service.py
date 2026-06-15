# -*- coding: utf-8 -*-
"""
入口服务：文件类型识别与状态初始化
节点：node_entry
功能：根据本地文件路径识别文件类型，自动装配对应状态字段

与原项目差异：增加多文件格式支持（txt/docx/xlsx/csv）
"""
from pathlib import Path
from app.shared.runtime.logger import step_log
from app.process.import_.agent.state import ImportGraphState

# 支持的文件格式
SUPPORTED_FORMATS = {
    ".md": "read_markdown",
    ".pdf": "parse_pdf",
    ".txt": "read_text",
    ".docx": "parse_docx",
    ".xlsx": "parse_xlsx",
    ".csv": "parse_csv",
}


@step_log("resolve_input_file")
def resolve_input_file(state: dict) -> ImportGraphState:
    """
    文件类型识别与状态初始化
    核心功能：根据本地文件路径识别文件类型，自动填充对应路径、路由开关、文件标题

    Args:
        state: 导入流程全局状态，必须包含 local_file_path 字段

    Returns:
        ImportGraphState: 补全文件信息后的完整状态对象
    """
    # 1. 获取文件本地路径
    local_file_path = state.get("local_file_path")

    # 2. 校验文件路径是否为空
    if not local_file_path:
        raise ValueError("local_file_path为空，无法继续业务")

    # 3. 提取文件信息
    path_obj = Path(local_file_path)
    file_ext = path_obj.suffix.lower()  # .md / .pdf / .txt / .docx / .xlsx / .csv
    file_title = path_obj.stem           # 文件名无后缀
    local_dir = str(path_obj.parent)     # 文件所在目录

    # 4. 校验文件格式是否支持
    if file_ext not in SUPPORTED_FORMATS:
        raise ValueError(f"不支持的文件类型: {file_ext}，支持的格式：{list(SUPPORTED_FORMATS.keys())}")

    # 5. 识别文件类型并设置对应状态与路由开关
    if file_ext == ".md":
        state["md_path"] = local_file_path
        state["is_md_read_enabled"] = True
        state["is_pdf_read_enabled"] = False
    elif file_ext == ".pdf":
        state["pdf_path"] = local_file_path
        state["is_pdf_read_enabled"] = True
        state["is_md_read_enabled"] = False
    elif file_ext == ".txt":
        # txt当作md处理
        state["md_path"] = local_file_path
        state["is_md_read_enabled"] = True
        state["is_pdf_read_enabled"] = False
    elif file_ext == ".docx":
        # docx需要先转换为md
        state["is_pdf_read_enabled"] = True  # 走PDF解析流程
        state["is_md_read_enabled"] = False
        state["pdf_path"] = local_file_path
    elif file_ext in [".xlsx", ".csv"]:
        # 表格文件需要特殊处理
        state["is_pdf_read_enabled"] = True  # 走PDF解析流程
        state["is_md_read_enabled"] = False
        state["pdf_path"] = local_file_path

    # 6. 自动提取文件标题
    state["file_title"] = file_title
    state["local_dir"] = local_dir
    state["file_ext"] = file_ext  # 记录文件后缀

    # 7. 返回补全后的状态
    return state
