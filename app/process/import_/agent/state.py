# 定义主图的全局state
import json
from typing import TypedDict, List
import copy
from app.shared.runtime.logger import logger


class ImportGraphState(TypedDict):
    """
    ImportGraphState 定义了整个导入流程中流转的数据结构。
    TypedDict 让我们在代码中能有自动补全和类型检查。
    使用字典式访问（如 state["task_id"]、state.get("chunks")）。
    """
    # ==================== 任务状态追踪 ====================
    task_id: str  # 每次调用流程的标识

    # ==================== 文件状态判断 ====================
    is_md_read_enabled: bool  # 是否为 MD 文件
    is_pdf_read_enabled: bool  # 是否为 PDF 文件

    # ==================== 地址路径 ====================
    local_file_path: str  # 存储要解析的 pdf/md 地址
    local_dir: str  # 存储生成的 md 文件
    md_path: str  # 专门存储 md 地址
    pdf_path: str  # 专门存储 pdf 地址
    file_title: str  # 存储文件名称，无后缀
    file_ext: str  # 文件后缀（.md/.pdf/.txt/.docx/.xlsx/.csv）

    # ==================== 文本和切块内容 ====================
    md_content: str  # 读取 md 内容用于切片
    item_name: str  # 模型识别的一个文档对应的名称
    chunks: list  # 存储切块的内容
    embeddings_content: list  # 存储带有切块的内容

    # ==================== 元数据（新增） ====================
    doc_id: str  # 文档 ID
    doc_type: str  # 文档类型（maintenance_manual/warranty_manual/repair_manual/typical_case/faq）
    vehicle_model: str  # 车型（如 T5、T7）
    component: str  # 部件（如 发动机、电池）
    version: str  # 版本号（如 v1.0）
    effective_date: str  # 生效日期（格式 YYYY-MM-DD）
    expire_date: str  # 失效日期（格式 YYYY-MM-DD）
    visible_roles: List[str]  # 可见角色列表
    document_state: str  # 文档状态（uploaded/parsing/parsed/pending_review/published/rejected/offline）
    knowledge_doc_id: str  # MongoDB知识文档ID（新增）
    import_status: str  # 导入状态（新增）


# 提供下对外快速创建的方法
# 模板
default_state: ImportGraphState = {
    'task_id': '',
    'is_md_read_enabled': False,
    'is_pdf_read_enabled': False,
    'local_file_path': '',
    'local_dir': '',
    'md_path': '',
    'pdf_path': '',
    'file_title': '',
    'file_ext': '',
    'item_name': '',
    'chunks': [],
    'embeddings_content': [],
    'md_content': '',
    # 新增字段
    'doc_id': '',
    'doc_type': 'faq',
    'vehicle_model': '',
    'component': '',
    'version': 'v1.0',
    'effective_date': '',
    'expire_date': '',
    'visible_roles': ['customer', 'service_advisor'],
    'document_state': 'uploaded',
    'knowledge_doc_id': '',
    'import_status': '',
}


def create_default_state(**overrides) -> ImportGraphState:
    """
    创建导入流程的默认状态，支持覆盖字段
    
    :param overrides: 传入的参数 key=value
    :return: 每次返回是基于模板创建的新的字典对象
    """
    copy_state = copy.deepcopy(default_state)
    copy_state.update(overrides)
    return copy_state


def get_default_state() -> ImportGraphState:
    """
    返回一个新的状态实例，避免全局变量污染。
    """
    return copy.deepcopy(default_state)


if __name__ == '__main__':
    state = create_default_state(task_id="task_007")
    logger.info(f"测试复制方法: \n {json.dumps(state, ensure_ascii=False, indent=4)}")

    state1 = create_default_state()
    logger.info(f"测试复制方法: \n{json.dumps(state1, ensure_ascii=False, indent=4)}")
