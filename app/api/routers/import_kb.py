"""
知识库导入路由。

把"上传 + 触发导入流程 + 任务状态查询 + 测试页面"
四个 HTTP 入口收敛到 page 层（[import_page.py](file:///d:/heimaAI/PytorchSDXX/08_掌柜智库/实战/实战/auto-carcrm/app/process/import_/page/import_page.py)），
路由层只做参数解析与响应包装，不直接接触 LangGraph。

接口清单（所有接口挂载在 /api/v1/knowledge 之下）：

- ``POST /api/v1/knowledge/upload``   上传文件并异步触发导入
- ``GET  /api/v1/knowledge/status/{task_id}``   查询任务状态
- ``GET  /api/v1/knowledge/html``     返回导入测试页
"""
from __future__ import annotations

from mimetypes import guess_type
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, Form

from app.core.dependencies import CurrentUser, get_current_user
from app.core.response import success_response
from app.process.import_.page.import_page import import_page
from app.shared.runtime.logger import logger
from app.shared.utils.path_util import PROJECT_ROOT

router = APIRouter(prefix='/knowledge', tags=['knowledge-import'])


@router.post('/upload')
def upload_documents(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description='待导入的知识文件（当前取第一个）'),
    doc_type: str = Form('', description='文档类型'),
    vehicle_model: str = Form('', description='适用车型'),
    version: str = Form('', description='版本号'),
    component: str = Form('', description='适用部件'),
    effective_date: str = Form('', description='生效日期'),
    expire_date: str = Form('', description='失效日期'),
    visible_roles: str = Form('all', description='可见角色'),
    remark: str = Form('', description='备注说明'),
    user: CurrentUser = Depends(get_current_user),
):
    """
    上传一个或多个文件并异步触发 LangGraph 导入流程。

    当前实现：
    - 仅取第一个文件（与既有 import_server 行为一致），其余文件忽略。
    - 通过 FastAPI BackgroundTasks 异步执行，HTTP 立即返回 task_id。

    Returns:
        ``{code, message, data: {task_ids, user_id}}``
    """
    # 构建元数据字典
    meta = {
        'doc_type': doc_type,
        'vehicle_model': vehicle_model,
        'version': version,
        'component': component,
        'effective_date': effective_date,
        'expire_date': expire_date,
        'visible_roles': visible_roles,
        'remark': remark,
    }
    
    result = import_page.upload_and_invoke(
        files=files,
        background_tasks=background_tasks,
        user_id=user.user_id,
        meta=meta,
    )
    logger.info(
        f"[import_kb.upload] user={user.user_id} "
        f"task_ids={result.get('task_ids')}"
    )
    return success_response(result, message='知识文件已接收，导入任务已下发')


@router.get('/status/{task_id}')
def get_task_status(
    task_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """
    查询指定 task_id 的导入状态。

    Returns:
        ``{code, message, data: {task_id, status, done_list, running_list}}``
    """
    status = import_page.get_status(task_id)
    return success_response(status, message='知识导入任务状态查询成功')


@router.get('/html')
def import_html():
    """
    返回导入测试页（[app/resources/html/import.html](file:///d:/heimaAI/PytorchSDXX/08_掌柜智库/实战/实战/auto-carcrm/app/resources/html/import.html)）。

    缺失时给出 404 文案，避免把整个接口挂掉。
    """
    html_path: Path = PROJECT_ROOT / 'app' / 'resources' / 'html' / 'import.html'
    if not html_path.exists():
        logger.warning(f"[import_kb.html] 测试页不存在：{html_path}")
        return success_response(
            {
                'html_path': str(html_path),
                'hint': '请将前端 import.html 放到上述路径后重启服务',
            },
            message='导入测试页尚未就位',
        )
    from fastapi.responses import FileResponse  # 局部导入，保持顶部依赖整洁

    return FileResponse(
        path=html_path,
        media_type=guess_type(html_path.name)[0] or 'text/html',
    )
