"""
查询/对话页面层（page）：HTTP 路由与 LangGraph 之间的页面级编排门面。

职责：
- 把"触发 query graph、SSE 推送、历史记录读写"等编排逻辑从 HTTP 层下沉到 page 层
- 为 router 提供稳定的方法签名（`ask`、`get_history`、`clear_history`）
- 屏蔽底层 LangGraph、sse_utils、history_repository 的细节
"""
from app.process.query.page.query_page import QueryPage, query_page

__all__ = ["QueryPage", "query_page"]
