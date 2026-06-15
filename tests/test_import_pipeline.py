# -*- coding: utf-8 -*-
"""
正向流程测试：用真实 PDF 文件跑完整条 import 链路
用法：在项目根目录运行 python tests/test_import_pipeline.py

链路：entry → pdf_to_md → md_img → split → item_name → embedding → milvus → doc_meta → save_knowledge → publish

需要：MongoDB / Milvus / MinIO / Embedding模型 / MinerU 都已启动
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.process.import_.agent.state import create_default_state
from app.process.import_.agent.main_graph import kb_import_app, after_entry_node
from app.shared.runtime.logger import logger
from app.shared.utils.path_util import PROJECT_ROOT


def emit(message: str):
    print(message, flush=True)
    logger.info(message)


def test_import_pipeline_sanbao():
    """正向流程测试：三包手册.pdf"""
    pdf_file = "三包手册.pdf"
    task_id = "test_sanbao_001"

    emit("=" * 60)
    emit(f"开始正向流程测试: {pdf_file}")
    emit("=" * 60)

    test_pdf_path = os.path.join(PROJECT_ROOT, "doc", pdf_file)
    test_output_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(test_output_dir, exist_ok=True)

    emit(f"项目根目录: {PROJECT_ROOT}")
    emit(f"测试PDF路径: {test_pdf_path}")
    emit(f"输出目录: {test_output_dir}")

    if not os.path.exists(test_pdf_path):
        emit(f"PDF 文件不存在: {test_pdf_path}")
        assert False, f"PDF 文件不存在: {test_pdf_path}"

    emit("PDF 文件检查通过")
    emit("开始构造初始 state")

    test_state = create_default_state(
        task_id=task_id,
        local_file_path=test_pdf_path,
        local_dir=test_output_dir,
        file_ext=".pdf",
    )

    emit(f"初始状态构造完成，task_id={task_id}")
    emit(f"state.file_ext={test_state.get('file_ext')}")
    emit(f"state.local_file_path={test_state.get('local_file_path')}")
    emit("开始预判入口路由")

    route = after_entry_node(test_state)
    emit(f"入口路由预判结果: {route}")
    emit("准备进入 LangGraph stream")

    final_state = None
    step_count = 0

    try:
        stream_iter = kb_import_app.stream(test_state, stream_mode="values")
        emit("LangGraph stream 已创建，开始迭代")

        for step in stream_iter:
            step_count += 1
            if isinstance(step, dict):
                step_keys = list(step.keys())
                current_node = step_keys[-1] if step_keys else "空状态"
            else:
                current_node = f"非dict返回: {type(step).__name__}"
            emit(f"节点 {step_count} 执行完成: {current_node}")
            final_state = step
    except Exception as e:
        emit(f"全流程执行失败（节点 {step_count} 之后）: {e}")
        logger.exception(f"全流程执行失败（节点 {step_count} 之后）: {e}")
        assert False, f"全流程执行失败: {e}"

    if final_state:
        emit("=" * 60)
        emit("全流程执行成功！")
        emit("=" * 60)
        chunks = final_state.get("chunks", [])
        emit(f"切片数: {len(chunks)}")
        emit(f"主体名: {final_state.get('item_name', '未识别')}")
        emit(f"文档类型: {final_state.get('doc_type', '未识别')}")
        emit(f"车型: {final_state.get('vehicle_model', '未识别')}")
        emit(f"文档状态: {final_state.get('document_state', '未知')}")
        emit(f"knowledge_doc_id: {final_state.get('knowledge_doc_id', '无')}")
        if chunks:
            emit(f"第一块内容预览: {chunks[0].get('content', '')[:100]}...")
        emit("=" * 60)
    else:
        emit("全流程执行完成但未获取到最终状态")
        assert False, "全流程执行完成但未获取到最终状态"
