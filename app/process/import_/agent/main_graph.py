# -*- coding: utf-8 -*-
"""
导入流程主图
作用：串联所有导入节点，定义执行顺序
参考老师 main_graph.py 的代码风格
"""
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from app.shared.runtime.logger import logger

# 导入自定义状态类
from app.process.import_.agent.state import ImportGraphState, create_default_state

# 导入所有自定义业务节点
from app.process.import_.agent.nodes.node_entry import node_entry
from app.process.import_.agent.nodes.node_pdf_to_md import node_pdf_to_md
from app.process.import_.agent.nodes.node_md_img import node_md_img
from app.process.import_.agent.nodes.node_document_split import node_document_split
from app.process.import_.agent.nodes.node_item_name_recognition import node_item_name_recognition
from app.process.import_.agent.nodes.node_bge_embedding import node_bge_embedding
from app.process.import_.agent.nodes.node_import_milvus import node_import_milvus

# 导入新增节点
from app.process.import_.agent.nodes.node_doc_meta import node_doc_meta
from app.process.import_.agent.nodes.node_save_knowledge import node_save_knowledge
from app.process.import_.agent.nodes.node_publish import node_publish


# 初始化环境变量
load_dotenv()


# 1. 定义状态图对象
main_graph = StateGraph(ImportGraphState)

# 2. 添加节点
main_graph.add_node("node_entry", node_entry)
main_graph.add_node("node_pdf_to_md", node_pdf_to_md)
main_graph.add_node("node_md_img", node_md_img)
main_graph.add_node("node_document_split", node_document_split)
main_graph.add_node("node_item_name_recognition", node_item_name_recognition)
main_graph.add_node("node_bge_embedding", node_bge_embedding)
main_graph.add_node("node_import_milvus", node_import_milvus)

# 添加新增节点
main_graph.add_node("node_doc_meta", node_doc_meta)
main_graph.add_node("node_save_knowledge", node_save_knowledge)
main_graph.add_node("node_publish", node_publish)


# 3. 指定入口节点
main_graph.set_entry_point("node_entry")


# 4. 设置入口节点后的条件边
def after_entry_node(state: ImportGraphState):
    """
    node_entry 之后的路由逻辑
    
    判断：
    - 如果是 MD 文件，跳转到 node_md_img
    - 如果是 PDF 文件，跳转到 node_pdf_to_md
    - 否则，跳转到 END
    """
    if state['is_md_read_enabled']:
        logger.info(f"node_entry节点判断文件{state['local_file_path']}类型md，跳转到：node_md_img")
        return "node_md_img"
    elif state['is_pdf_read_enabled']:
        logger.info(f"node_entry节点判断文件{state['local_file_path']}类型pdf，跳转到：node_pdf_to_md")
        return "node_pdf_to_md"
    else:
        logger.warning(f"node_entry节点获取的文件{state['local_file_path']}无法处理对应的类型，跳转到：END节点")
        return END


main_graph.add_conditional_edges(
    "node_entry",
    after_entry_node,
    {
        "node_md_img": "node_md_img",
        "node_pdf_to_md": "node_pdf_to_md",
        END: END
    }
)


# 5. 设置静态边
# PDF → MD → 图片处理 → 文档切分 → 主体识别 → 向量化 → Milvus入库 → 元数据抽取 → 知识保存 → 审核发布 → END
main_graph.add_edge("node_pdf_to_md", "node_md_img")
main_graph.add_edge("node_md_img", "node_document_split")
main_graph.add_edge("node_document_split", "node_item_name_recognition")
main_graph.add_edge("node_item_name_recognition", "node_bge_embedding")
main_graph.add_edge("node_bge_embedding", "node_import_milvus")

# 新增节点
main_graph.add_edge("node_import_milvus", "node_doc_meta")
main_graph.add_edge("node_doc_meta", "node_save_knowledge")
main_graph.add_edge("node_save_knowledge", "node_publish")
main_graph.add_edge("node_publish", END)


# 6. 编译图对象
kb_import_app = main_graph.compile()

logger.info("导入图编译完成")


if __name__ == "__main__":
    from app.shared.utils.path_util import PROJECT_ROOT
    import os

    # 全流程测试
    logger.info("===== 开始执行知识导入全流程测试 =====")
    
    # 1. 构造测试文件路径
    test_pdf_name = os.path.join("doc", "hak180产品安全手册.pdf")
    test_pdf_path = os.path.join(PROJECT_ROOT, test_pdf_name)
    
    # 2. 构造输出目录
    test_output_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(test_output_dir, exist_ok=True)

    # 3. 校验测试PDF文件是否存在
    if not os.path.exists(test_pdf_path):
        logger.error(f"全流程测试失败：测试PDF文件不存在，路径：{test_pdf_path}")
    else:
        # 4. 构造测试状态
        test_state = create_default_state(
            task_id="test_import_workflow_001",
            local_file_path=test_pdf_path,
            local_dir=test_output_dir,
            is_pdf_read_enabled=True,
            is_md_read_enabled=False
        )
        
        try:
            logger.info(f"测试任务启动，PDF文件路径：{test_pdf_path}")
            
            # 5. 执行 LangGraph 全流程
            final_state = None
            for step in kb_import_app.stream(test_state, stream_mode="values"):
                current_node = list(step.keys())[-1] if step else "未知节点"
                logger.info(f"✅ 节点执行完成：{current_node}")
                final_state = step

            # 6. 结果预览
            if final_state:
                logger.info("-" * 80)
                logger.info("===== 全流程测试执行成功 =====")
                chunks = final_state.get("chunks", [])
                logger.info(f"📝 文档切分总切片数：{len(chunks)}")
                logger.info(f"📄 文档类型：{final_state.get('doc_type')}")
                logger.info(f"🚗 车型：{final_state.get('vehicle_model')}")
                logger.info(f"📋 文档状态：{final_state.get('document_state')}")
                logger.info("-" * 80)
        except Exception as e:
            logger.exception(f"全流程测试运行失败：{e}")
    
    logger.info("===== 知识导入全流程测试结束 =====")
