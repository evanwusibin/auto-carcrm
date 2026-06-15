"""
知识导入页面层（page）门面。

负责将"接收上传 -> 触发 LangGraph 导入流程 -> 回写任务状态"
整体编排沉淀在 page 层，供 HTTP 路由层调用，避免 router 直接耦合 LangGraph。
"""
from __future__ import annotations

import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterable

from fastapi import UploadFile

from app.process.import_.agent.main_graph import kb_import_app
from app.process.import_.agent.state import create_default_state
from app.shared.runtime.logger import logger
from app.shared.utils.path_util import PROJECT_ROOT
from app.shared.utils.task_utils import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_PROCESSING,
    get_done_task_list,
    get_running_task_list,
    get_task_status,
    update_task_status,
)


# 状态映射：节点名 → 前端状态
NODE_STATUS_MAP = {
    "node_entry": "uploaded",
    "node_pdf_to_md": "parsing",
    "node_md_img": "parsing",
    "node_document_split": "split",
    "node_item_name_recognition": "split",
    "node_bge_embedding": "embedding",
    "node_import_milvus": "indexing",
    "node_doc_meta": "indexing",
    "node_save_knowledge": "indexing",
    "node_publish": "completed",
}


class ImportPage:
    """
    知识导入页面门面：把"上传 + 触发图 + 状态"打包成一个稳定的 page 接口。
    """

    # ---------- 1. 上传 + 触发图 ----------
    def upload_and_invoke(
        self,
        *,
        files: Iterable[UploadFile],
        background_tasks,
        user_id: str = "anonymous",
        meta: dict = None,
    ) -> dict:
        """
        接收上传文件，保存到本地后异步触发 LangGraph 导入流程。
        """
        files = list(files)
        if not files:
            logger.warning(f"[ImportPage] 用户 {user_id} 提交空文件列表")
            return {"task_ids": [], "user_id": user_id}

        task_id = str(uuid.uuid4())
        local_dir = (
            PROJECT_ROOT
            / "output"
            / datetime.now().strftime("%Y%m%d%H%M%S")
            / task_id
        )
        local_dir.mkdir(parents=True, exist_ok=True)

        # 当前仅取第一个文件
        current_file = files[0]
        local_file_path = local_dir / current_file.filename

        with local_file_path.open("wb") as buffer:
            shutil.copyfileobj(current_file.file, buffer)

        logger.info(
            f"[ImportPage] 文件已落盘，user={user_id} task_id={task_id} "
            f"path={local_file_path}"
        )

        background_tasks.add_task(
            self._invoke_graph,
            task_id=task_id,
            local_file_path=local_file_path,
            local_dir=local_dir,
            meta=meta,
        )

        return {"task_ids": [task_id], "user_id": user_id}

    # ---------- 2. 状态查询 ----------
    def get_status(self, task_id: str) -> dict:
        """
        查询导入任务的执行状态。
        """
        return {
            "task_id": task_id,
            "status": get_task_status(task_id) or "unknown",
            "done_list": get_done_task_list(task_id),
            "running_list": get_running_task_list(task_id),
        }

    # ---------- 3. 内部：触发 LangGraph ----------
    def _invoke_graph(
        self,
        *,
        task_id: str,
        local_file_path: Path,
        local_dir: Path,
        meta: dict = None,
    ) -> None:
        """
        实际拉起 LangGraph 导入流程的后台执行体。
        """
        state = create_default_state(
            task_id=task_id,
            local_file_path=str(local_file_path),
            local_dir=str(local_dir),
        )
        
        # 将表单元数据添加到 state 中
        if meta:
            state['doc_type'] = meta.get('doc_type', '')
            state['vehicle_model'] = meta.get('vehicle_model', '')
            state['version'] = meta.get('version', '')
            state['component'] = meta.get('component', '')
            state['effective_date'] = meta.get('effective_date', '')
            state['expire_date'] = meta.get('expire_date', '')
            state['visible_roles'] = [meta.get('visible_roles', 'all')]
        
        try:
            update_task_status(task_id, TASK_STATUS_PROCESSING)
            logger.info(f"[ImportPage] 导入图开始执行 task_id={task_id}")

            for step in kb_import_app.stream(state, stream_mode="updates"):
                for node_name, node_output in step.items():
                    if node_name in NODE_STATUS_MAP:
                        frontend_status = NODE_STATUS_MAP[node_name]
                        update_task_status(task_id, frontend_status)
                        logger.info(f"[ImportPage] 节点 {node_name} 完成，状态更新为 {frontend_status}")

            logger.info(f"[ImportPage] 导入图执行成功 task_id={task_id}")
            update_task_status(task_id, TASK_STATUS_COMPLETED)

        except Exception:
            update_task_status(task_id, TASK_STATUS_FAILED)
            logger.exception(f"[ImportPage] 导入图执行失败 task_id={task_id}")


# 全局门面单例
import_page = ImportPage()
