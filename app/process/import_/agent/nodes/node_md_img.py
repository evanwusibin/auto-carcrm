"""
应用主包 / 导入流程兼容层 / 图编排子模块 / 节点适配层中的 node_md_img 模块，负责承载对应场景的具体实现逻辑。
"""
import os
from app.shared.runtime.logger import logger, node_log
from app.shared.utils.task_utils import add_done_task, add_running_task
from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.enrich_markdown_images import enrich_markdown_images

@node_log("node_md_img")
def node_md_img(state: ImportGraphState) -> ImportGraphState:
    """
    节点: 图片处理 (node_md_img)
    为什么叫这个名字: 处理 Markdown 中的图片资源 (Image)。
    """
    # 图片增强节点启动后，后续会补齐图片摘要并替换 Markdown 中的引用。
    add_running_task(state["task_id"], "node_md_img")
    # 真正的图片扫描、总结、上传和替换逻辑都在 service 层完成。
    state = enrich_markdown_images(state)
    add_done_task(state["task_id"], "node_md_img")
    return state

if __name__ == "__main__":
    """本地测试入口：单独运行该文件时，执行MD图片处理全流程测试"""
    # print(mimetypes.guess_type("mv.jpg"))
    # print(mimetypes.guess_type("mv.png"))
    from app.shared.utils.path_util import PROJECT_ROOT
    from app.shared.runtime.logger import logger
    logger.info(f"本地测试 - 项目根目录：{PROJECT_ROOT}")

    # 测试MD文件路径（需手动将测试文件放入对应目录）
    test_md_name = os.path.join(r"output\hak180使用说明书", "hak180使用说明书.md")
    test_md_path = os.path.join(PROJECT_ROOT, test_md_name)

    # 校验测试文件是否存在
    if not os.path.exists(test_md_path):
        logger.error(f"本地测试 - 测试文件不存在：{test_md_path}")
        logger.info("请检查文件路径，或手动将测试MD文件放入项目根目录的output目录下")
    else:
        # 构造测试状态对象，模拟流程入参
        test_state = {
            "md_path": test_md_path,
            "task_id": "test_task_123456",
            "md_content": ""
        }
        logger.info("开始本地测试 - MD图片处理全流程")
        # 执行核心处理流程
        result_state = node_md_img(test_state)
        logger.info(f"本地测试完成 - 处理结果状态：{result_state}")
