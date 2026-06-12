"""
知识导入页面层（page）：HTTP 路由与 LangGraph 之间的页面级编排门面。

职责：
- 把上传文件、触发 import graph、记录任务状态等编排逻辑从 HTTP 层下沉到 page 层
- 为 router 提供稳定的方法签名（`upload_and_invoke`、`get_status`）
- 屏蔽底层 LangGraph 与 task_utils 的细节，方便后续扩展（权限、通知、回写 Mongo 等）
"""
from app.process.import_.page.import_page import ImportPage, import_page

__all__ = ["ImportPage", "import_page"]
