# -*- coding: utf-8 -*-
"""用户反馈路由（有用/无用）"""
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.response import success_response
from app.infra.persistence.qa_repository import qa_repository
from app.shared.clients.mongo_business_utils import get_business_db
from app.shared.runtime.logger import logger

router = APIRouter(prefix="/feedback", tags=["反馈"])


class FeedbackRequest(BaseModel):
    """反馈请求"""
    session_id: str = Field(..., description="会话ID")
    query: str = Field(..., description="用户问题")
    answer: str = Field(..., description="AI回答")
    feedback_type: str = Field(..., description="反馈类型: useful/useless")
    comment: str | None = Field(None, description="用户评论（可选）")


def get_feedback_collection():
    return get_business_db()["user_feedbacks"]


@router.post("/submit", summary="提交反馈")
async def submit_feedback(feedback: FeedbackRequest):
    """提交用户反馈，并持久化本次问题与回答。"""
    if feedback.feedback_type not in ["useful", "useless"]:
        return success_response(
            None,
            message="feedback_type必须是useful或useless",
            code=400,
        )

    feedback_data = {
        "session_id": feedback.session_id,
        "query": feedback.query,
        "answer": feedback.answer,
        "feedback_type": feedback.feedback_type,
        "comment": feedback.comment,
        "created_at": datetime.now().isoformat(),
    }

    try:
        inserted_id = qa_repository.save_feedback(feedback_data)
        logger.info(
            f"[feedback.submit] session_id={feedback.session_id} "
            f"type={feedback.feedback_type} inserted_id={inserted_id}"
        )
        return success_response(
            {
                "id": str(inserted_id) if inserted_id else "",
                "feedback_type": feedback.feedback_type,
                "session_id": feedback.session_id,
                "query": feedback.query,
                "answer": feedback.answer,
            },
            message="反馈提交成功",
            code=200,
        )
    except Exception as exc:
        logger.exception(f"[feedback.submit] 保存反馈失败: {exc}")
        return success_response(
            None,
            message=f"反馈保存失败: {str(exc)}",
            code=500,
        )


@router.get("/stats", summary="获取反馈统计")
async def get_feedback_stats():
    """获取反馈统计信息"""
    try:
        col = get_feedback_collection()
        useful_count = col.count_documents({"feedback_type": "useful"})
        useless_count = col.count_documents({"feedback_type": "useless"})
        total = useful_count + useless_count
        return success_response(
            {
                "total": total,
                "useful": useful_count,
                "useless": useless_count,
                "useful_rate": round(useful_count / total * 100, 2) if total > 0 else 0,
            },
            message="反馈统计查询成功",
            code=200,
        )
    except Exception as exc:
        logger.exception(f"[feedback.stats] 查询失败: {exc}")
        return success_response(None, message=f"反馈统计查询失败: {str(exc)}", code=500)


@router.get("/list", summary="获取反馈列表")
async def get_feedback_list(limit: int = 20):
    """获取最近的反馈列表"""
    try:
        col = get_feedback_collection()
        feedbacks = []
        for item in col.find().sort("created_at", -1).limit(limit):
            item["id"] = str(item.pop("_id"))
            feedbacks.append(item)
        return success_response(feedbacks, message="反馈列表查询成功", code=200)
    except Exception as exc:
        logger.exception(f"[feedback.list] 查询失败: {exc}")
        return success_response(None, message=f"反馈列表查询失败: {str(exc)}", code=500)
