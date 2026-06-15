"""
对话 / 问答路由。

把"问答主入口 + SSE 流式推送 + 历史记录 + 测试页"
全部收敛到 page 层（[query_page.py](file:///d:/heimaAI/PytorchSDXX/08_掌柜智库/实战/实战/auto-carcrm/app/process/query/page/query_page.py)），
路由层只做参数解析、依赖注入与响应包装，不直接接触 LangGraph / SSE 队列。

接口清单（所有接口挂载在 /api/v1/chat 之下）：

- ``POST   /api/v1/chat/query``               触发一次问答（同步/流式均可）
- ``GET    /api/v1/chat/stream/{session_id}`` SSE 订阅流（前端 EventSource）
- ``GET    /api/v1/chat/history/{session_id}`` 拉取历史
- ``DELETE /api/v1/chat/history/{session_id}`` 清空历史
- ``GET    /api/v1/chat/html``                返回 chat 测试页
"""
from __future__ import annotations

from mimetypes import guess_type
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from app.core.dependencies import CurrentUser, get_current_user
from app.core.response import success_response
from app.process.query.page.query_page import query_page
from app.shared.runtime.logger import logger
from app.shared.utils.path_util import PROJECT_ROOT
from app.shared.utils.sse_utils import sse_generator

router = APIRouter(prefix='/chat', tags=['chat'])


# ---------- 1. 问答主入口 ----------
@router.post('/query')
def chat_query(
    background_tasks: BackgroundTasks,
    payload: dict[str, Any],
    user: CurrentUser = Depends(get_current_user),
):
    """
    触发一次问答。

    Body::

        {
            "query": "用户问题",
            "session_id": "可选，不传则自动生成",
            "is_stream": true/false
        }

    - ``is_stream=false``：当前线程同步等待结果返回。
    - ``is_stream=true``：仅下发任务，结果通过
      ``GET /api/v1/chat/stream/{session_id}`` SSE 推送。
    """
    query: str = (payload or {}).get('query') or ''
    session_id: str | None = (payload or {}).get('session_id')
    is_stream: bool = bool((payload or {}).get('is_stream', False))

    if not query.strip():
        return success_response(
            {'hint': 'query 不能为空'},
            message='参数错误',
            code=400,
        )

    result = query_page.ask(
        query=query,
        session_id=session_id,
        is_stream=is_stream,
        background_tasks=background_tasks,
        user_id=user.user_id,
    )
    return success_response(
        result,
        message=(
            '流式任务已下发，订阅 /chat/stream/{session_id} 接收结果'
            if is_stream
            else '问答流程已执行完毕'
        ),
    )


# ---------- 2. SSE 订阅流 ----------
@router.get('/stream/{session_id}')
def chat_stream(session_id: str, request: Request):
    """
    SSE 流式订阅。

    前端通过 ``new EventSource('/api/v1/chat/stream/{session_id}')`` 订阅，
    事件类型包括 ``ready / progress / delta / final / error / __close__``。
    """
    return StreamingResponse(
        sse_generator(session_id, request),
        media_type='text/event-stream',
    )


# ---------- 3. 历史记录 ----------
def _serialize_items(items: list[dict]) -> list[dict]:
    """将 MongoDB 文档转为可 JSON 序列化的 dict（ObjectId → str）。"""
    result = []
    for item in items:
        row = {}
        for k, v in item.items():
            if k == '_id':
                row[k] = str(v)
            elif hasattr(v, 'isoformat'):
                row[k] = v.isoformat()
            else:
                row[k] = v
        result.append(row)
    return result


@router.get('/sessions')
def chat_sessions(
    limit: int = Query(20, ge=1, le=100, description='最多返回多少个会话'),
    user: CurrentUser = Depends(get_current_user),
):
    """获取所有会话列表（按最近活跃时间倒序）。"""
    items = query_page.get_sessions(limit=limit)
    return success_response(
        {'items': _serialize_items(items)},
        message='会话列表查询成功',
    )


@router.get('/history/{session_id}')
def chat_history(
    session_id: str,
    limit: int = Query(10, ge=1, le=200, description='返回最近 N 条历史'),
    user: CurrentUser = Depends(get_current_user),
):
    """拉取指定 session 的历史消息（按时间倒序最近 limit 条）。"""
    items = query_page.get_history(session_id=session_id, limit=limit)
    return success_response(
        {'session_id': session_id, 'limit': limit, 'items': _serialize_items(items)},
        message='历史记录查询成功',
    )


@router.delete('/history/{session_id}')
def chat_clear_history(
    session_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """清空指定 session 的历史消息，返回被删除条数。"""
    deleted = query_page.clear_history(session_id=session_id)
    logger.info(
        f"[chat.clear_history] user={user.user_id} session_id={session_id} "
        f"deleted={deleted}"
    )
    return success_response(
        {'session_id': session_id, 'deleted_count': deleted},
        message=f'历史记录已清空，删除 {deleted} 条',
    )


# ---------- 4. 测试页 ----------
@router.get('/html')
def chat_html():
    """
    返回对话测试页（[app/resources/html/chat.html](file:///d:/heimaAI/PytorchSDXX/08_掌柜智库/实战/实战/auto-carcrm/app/resources/html/chat.html)）。

    缺失时给出 404 文案，避免把整个接口挂掉。
    """
    html_path: Path = PROJECT_ROOT / 'app' / 'resources' / 'html' / 'chat.html'
    if not html_path.exists():
        logger.warning(f"[chat.html] 测试页不存在：{html_path}")
        return success_response(
            {
                'html_path': str(html_path),
                'hint': '请将前端 chat.html 放到上述路径后重启服务',
            },
            message='对话测试页尚未就位',
        )

    return FileResponse(
        path=html_path,
        media_type=guess_type(html_path.name)[0] or 'text/html',
    )
