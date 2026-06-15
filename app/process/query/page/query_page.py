"""
查询/对话页面层（page）门面。

负责将"接收查询 -> 触发 LangGraph query 流程 -> 推送 SSE 事件 -> 落历史记录"
整体编排沉淀在 page 层，供 HTTP 路由层调用，避免 router 直接耦合 LangGraph。

# TODO(you): 后续可在此处补充业务逻辑：
#   - 在 ask 入口调用 domain/diagnosis_service / repair_service 等做意图分流
#   - 在 ask 出口结合 infra/persistence/history_repository 落库（已经接好示例）
#   - 在 SSE 流式输出过程中按 token 推送（结合 LLM stream + sse_utils）
"""
from __future__ import annotations

import uuid
from typing import Any

from app.infra.persistence.history_repository import history_repository
from app.process.query.agent.main_graph import query_graph_app
from app.process.query.agent.state import create_query_default_state
from app.shared.runtime.logger import logger
from app.shared.utils.sse_utils import SSEEvent, create_sse_queue, push_to_session
from app.shared.utils.task_utils import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_PROCESSING,
    clear_task,
    get_done_task_list,
    update_task_status,
)


class QueryPage:
    """
    查询页面门面：把"问答 + 流式推送 + 历史记录"打包成一个稳定的 page 接口。

    使用方式（HTTP 路由）::

        @router.post('/query')
        def query(payload: QueryRequestParam, background_tasks: BackgroundTasks):
            return query_page.ask(
                query=payload.query,
                session_id=payload.session_id,
                is_stream=payload.is_stream,
                background_tasks=background_tasks,
            )
    """

    # ---------- 1. 问答主接口 ----------
    def ask(
        self,
        *,
        query: str,
        session_id: str | None = None,
        is_stream: bool = False,
        background_tasks=None,
        user_id: str = "anonymous",
    ) -> dict:
        """
        触发查询流程，分流式 / 非流式两种执行路径。

        Args:
            query: 用户原始问题。
            session_id: 会话 ID；为空时自动生成。
            is_stream: 是否流式响应。流式会通过 SSE 推送结果。
            background_tasks: FastAPI 的后台任务对象（流式必传，非流式可选）。
            user_id: 当前用户 ID（用于审计）。

        Returns:
            dict: 同步模式下返回 ``{"session_id", "answer", "done_list", "image_urls"}``，
                  流式模式下返回 ``{"session_id"}``，结果通过 SSE 推送。
        """
        session_id = session_id or str(uuid.uuid4())
        clear_task(session_id)

        # ---------- 流式：注册 SSE 队列 + 后台异步触发 ----------
        if is_stream:
            if background_tasks is None:
                raise ValueError("流式调用必须提供 background_tasks")
            create_sse_queue(session_id)
            background_tasks.add_task(
                self._invoke_graph,
                session_id=session_id,
                query=query,
                is_stream=True,
            )
            logger.info(f"[QueryPage] 流式任务已下发 session_id={session_id}")
            return {"session_id": session_id, "is_stream": True, "user_id": user_id}

        # ---------- 非流式：当前线程执行，等结果返回 ----------
        final_state = self._invoke_graph(
            session_id=session_id,
            query=query,
            is_stream=False,
        ) or {}

        refs = _build_refs(final_state)
        routes = _build_routes(final_state)
        risk = _build_risk(final_state)

        return {
            "session_id": session_id,
            "is_stream": False,
            "answer": final_state.get("answer", ""),
            "done_list": get_done_task_list(session_id),
            "image_urls": final_state.get("image_urls") or [],
            "candidate_item_names": final_state.get("candidate_item_names") or [],
            "refs": refs,
            "routes": routes,
            "risk": risk,
            "user_id": user_id,
        }

    # ---------- 2. 历史记录 ----------
    def get_sessions(self, limit: int = 20) -> list[dict]:
        """获取所有会话列表。"""
        return history_repository.list_sessions(limit=limit)

    def get_history(self, session_id: str, limit: int = 10) -> list[dict]:
        """读取最近的历史消息（默认 10 条）。"""
        return history_repository.list_recent(session_id, limit=limit)

    def clear_history(self, session_id: str) -> int:
        """清空指定会话的历史消息，返回删除条数。"""
        deleted = history_repository.clear_session(session_id)
        logger.info(
            f"[QueryPage] 清空历史 session_id={session_id} deleted={deleted}"
        )
        return deleted

    # ---------- 3. 内部：触发 LangGraph ----------
    def _invoke_graph(
        self,
        *,
        session_id: str,
        query: str,
        is_stream: bool,
    ) -> dict[str, Any] | None:
        """
        实际拉起 query graph 的执行体，同步/异步均复用。
        """
        state = create_query_default_state(
            session_id=session_id,
            original_query=query,
            is_stream=is_stream,
        )
        try:
            update_task_status(session_id, TASK_STATUS_PROCESSING, is_stream)
            logger.info(f"[QueryPage] 查询图开始执行 session_id={session_id}")
            result_state = query_graph_app.invoke(state)
            logger.info(
                f"[QueryPage] 查询图执行成功 session_id={session_id} "
                f"answer_len={len(str(result_state.get('answer', '')))}"
            )
            update_task_status(session_id, TASK_STATUS_COMPLETED, is_stream)

            # 构建前端需要的 refs/routes/risk
            refs = _build_refs(result_state)
            routes = _build_routes(result_state)
            risk = _build_risk(result_state)

            # 流式：把最终结果通过 SSE 推送给前端
            if is_stream:
                push_to_session(
                    session_id,
                    SSEEvent.FINAL,
                    {
                        "answer": result_state.get("answer", ""),
                        "status": "completed",
                        "image_urls": result_state.get("image_urls") or [],
                        "candidate_item_names": result_state.get("candidate_item_names") or [],
                        "refs": refs,
                        "routes": routes,
                        "risk": risk,
                    },
                )
            return result_state
        except Exception:  # noqa: BLE001 - page 层兜底
            update_task_status(session_id, TASK_STATUS_FAILED, is_stream)
            logger.exception(f"[QueryPage] 查询图执行失败 session_id={session_id}")
            if is_stream:
                push_to_session(
                    session_id,
                    SSEEvent.ERROR,
                    {"message": "查询执行失败，请稍后再试"},
                )
            return None


def _build_refs(state: dict) -> list[dict]:
    """从 reranked_docs 构建前端需要的 refs 格式"""
    docs = state.get("reranked_docs") or state.get("rrf_chunks") or []
    refs = []
    for doc in docs[:10]:  # 最多取10条
        refs.append({
            "doc": doc.get("file_title") or doc.get("item_name") or "未知文档",
            "page": doc.get("part", ""),
            "section": doc.get("title") or doc.get("parent_title") or "",
            "text": (doc.get("content") or "")[:200],
            "score": round(doc.get("score", doc.get("distance", 0)), 4),
        })
    return refs


def _build_routes(state: dict) -> list[str]:
    """根据各路检索结果是否非空，判断激活了哪些路由"""
    routes = []
    if state.get("embedding_chunks") or state.get("hyde_embedding_chunks"):
        routes.append("vec")
    if state.get("keyword_chunks"):
        routes.append("kw")
    if state.get("structured_chunks"):
        routes.append("struct")
    if state.get("case_chunks"):
        routes.append("case")
    if state.get("web_search_docs"):
        routes.append("web")
    return routes


def _build_risk(state: dict) -> dict | None:
    """根据置信度判断是否有风险提示"""
    score = state.get("confidence_score", 1.0)
    if score < 0.3:
        return {"level": "high", "text": "检索置信度较低，答案可能不准确，建议人工核实"}
    if score < 0.6:
        return {"level": "med", "text": "检索置信度中等，建议结合实际情况参考"}
    return None


# 全局门面单例：供 router 直接 import 使用
query_page = QueryPage()
