"""
知识导入页面层（page）门面。

负责将"接收上传 -> 触发 LangGraph 导入流程 -> 回写任务状态"
整体编排沉淀在 page 层，供 HTTP 路由层调用，避免 router 直接耦合 LangGraph。

# TODO(you): 后续可在此处补充业务逻辑：
#   - 调用 domain/case_service 写入"知识导入审计日志"
#   - 调用 infra/persistence/knowledge_repository 落库
#   - 调用 infra/object_stroage/minio_gateway 把原文件归档
#   - 加入用户权限校验（结合 dependencies.CurrentUser）
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


class ImportPage:
    """
    知识导入页面门面：把"上传 + 触发图 + 状态"打包成一个稳定的 page 接口。

    使用方式（HTTP 路由）::

        @router.post('/upload')
        def upload(background_tasks: BackgroundTasks, files: list[UploadFile]):
            return import_page.upload_and_invoke(
                files=files,
                background_tasks=background_tasks,
                user_id=current_user.user_id,
            )
    """

    # ---------- 1. 上传 + 触发图 ----------
    def upload_and_invoke(
        self,
        *,
        files: Iterable[UploadFile],
        background_tasks,
        user_id: str = "anonymous",
    ) -> dict:
        """
        接收上传文件，保存到本地后异步触发 LangGraph 导入流程。

        Args:
            files: FastAPI 收到的上传文件列表。
            background_tasks: FastAPI 的后台任务对象，避免接口阻塞。
            user_id: 当前用户（来自 dependencies.CurrentUser），用于审计/隔离。

        Returns:
            dict: ``{"task_ids": [...], "user_id": ...}``，task_id 用于后续查询状态。
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

        # 当前仅取第一个文件（与现有 import_server 保持一致），如需多文件后续扩展
        current_file = files[0]
        local_file_path = local_dir / current_file.filename

        with local_file_path.open("wb") as buffer:
            # 流式拷贝，避免大文件占内存
            shutil.copyfileobj(current_file.file, buffer)

        logger.info(
            f"[ImportPage] 文件已落盘，user={user_id} task_id={task_id} "
            f"path={local_file_path}"
        )

        # TODO(you): 这里可补：写入知识库审计 / 上传 MinIO / 推送告警 等
        background_tasks.add_task(
            self._invoke_graph,
            task_id=task_id,
            local_file_path=local_file_path,
            local_dir=local_dir,
        )

        return {"task_ids": [task_id], "user_id": user_id}

    # ---------- 2. 状态查询 ----------
    def get_status(self, task_id: str) -> dict:
        """
        查询导入任务的执行状态（基于内存态 task_utils）。

        Args:
            task_id: 上传接口返回的 task_id。

        Returns:
            dict: ``{"task_id", "status", "done_list", "running_list"}``
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
    ) -> None:
        """
        实际拉起 LangGraph 导入流程的后台执行体。

        说明：
        - 本方法不会被 HTTP 直接调用，仅作为 BackgroundTasks 的执行体。
        - 异常会被吞掉但写日志，任务状态会被置为 FAILED。
        """
        state = create_default_state(
            task_id=task_id,
            local_file_path=str(local_file_path),
            local_dir=str(local_dir),
        )
        try:
            # update_task_status(task_id, TASK_STATUS_PROCESSING)
            update_task_status(task_id, TASK_STATUS_PROCESSING)
            logger.info(f"[ImportPage] 导入图开始执行 task_id={task_id}")
            final_state = kb_import_app.invoke(state)
            logger.info(
                f"[ImportPage] 导入图执行成功 task_id={task_id} "
                f"keys={list(final_state.keys()) if final_state else []}"
            )
            update_task_status(task_id, TASK_STATUS_COMPLETED)
        except Exception:  # noqa: BLE001 - page 层兜底
            update_task_status(task_id, TASK_STATUS_FAILED)
            logger.exception(f"[ImportPage] 导入图执行失败 task_id={task_id}")


# 全局门面单例：供 router 直接 import 使用
import_page = ImportPage()
