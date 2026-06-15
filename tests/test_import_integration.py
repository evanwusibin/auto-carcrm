# -*- coding: utf-8 -*-
"""
集成测试：import 链路全流程
用法：在项目根目录运行 python tests/test_import_integration.py
需要：MongoDB / Milvus / MinIO / Embedding模型 / MinerU 都已启动
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.process.import_.agent.state import create_default_state
from app.shared.runtime.logger import logger

# ============================================================
# 测试 1：entry_service — 文件类型识别
# ============================================================
def test_01_entry_service():
    from app.rag.import_.entry_service import resolve_input_file

    state = create_default_state(local_file_path="")
    try:
        resolve_input_file(state)
        assert False
    except ValueError:
        pass

    state = create_default_state(local_file_path="D:/test.md")
    result = resolve_input_file(state)
    assert result["is_md_read_enabled"] == True
    assert result["file_title"] == "test"
    logger.info("✅ 测试1 entry_service 通过")


# ============================================================
# 测试 2：doc_meta_service — 元数据抽取（纯逻辑，不依赖外部服务）
# ============================================================
def test_02_doc_meta_service():
    from app.rag.import_.doc_meta_service import extract_doc_meta

    state = create_default_state(
        file_title="T5轻卡保养手册V2.1",
        md_content="生效日期：2024-01-01，本手册适用于T5轻卡的定期保养",
    )
    result = extract_doc_meta(state)
    assert result["doc_type"] == "保养手册"
    assert "T5" in result["vehicle_model"] or result["vehicle_model"] != ""
    logger.info(f"✅ 测试2 doc_meta_service 通过，车型={result['vehicle_model']}，类型={result['doc_type']}")


# ============================================================
# 测试 3：split_service — 文档切分（纯逻辑，不依赖外部服务）
# ============================================================
def test_03_split_service():
    from app.rag.import_.split_service import split_document

    state = create_default_state(
        md_path="",
        md_content="# 第一章 保养\n\n保养内容\n\n# 第二章 维修\n\n维修内容",
        file_title="测试文档",
    )
    result = split_document(state)
    chunks = result.get("chunks", [])
    assert len(chunks) >= 2
    assert chunks[0]["file_title"] == "测试文档"
    logger.info(f"✅ 测试3 split_service 通过，切出 {len(chunks)} 块")


# ============================================================
# 测试 4：item_name_service — 主体识别（需要 LLM）
# ============================================================
def test_04_item_name_service():
    from app.rag.import_.item_name_service import recognize_and_index_item_name

    state = create_default_state(
        chunks=[
            {"file_title": "T5轻卡保养手册", "title": "# 保养概述", "parent_title": "", "content": "T5轻卡的保养周期为每5000公里一次"},
            {"file_title": "T5轻卡保养手册", "title": "# 保养项目", "parent_title": "", "content": "包括更换机油、检查刹车片等"},
        ],
        file_title="T5轻卡保养手册",
    )
    result = recognize_and_index_item_name(state)
    item_name = result.get("item_name", "")
    logger.info(f"✅ 测试4 item_name_service 通过，识别到主体: {item_name}")


# ============================================================
# 测试 5：embedding_service — 向量化（需要 Embedding 模型）
# ============================================================
def test_05_embedding_service():
    from app.rag.import_.embedding_service import generate_chunk_embeddings

    state = create_default_state(
        chunks=[
            {"file_title": "测试", "title": "# 标题", "parent_title": "", "content": "测试内容", "item_name": "测试主体"},
        ],
    )
    result = generate_chunk_embeddings(state)
    chunks = result.get("embeddings_content", [])
    assert len(chunks) >= 1
    assert "dense_vector" in chunks[0]
    assert "sparse_vector" in chunks[0]
    logger.info(f"✅ 测试5 embedding_service 通过，向量维度={len(chunks[0]['dense_vector'])}")


# ============================================================
# 测试 6：index_service — Milvus 入库（需要 Milvus）
# ============================================================
def test_06_index_service():
    from app.rag.import_.index_service import index_chunks

    state = create_default_state(
        chunks=[
            {
                "file_title": "测试文档",
                "title": "# 测试标题",
                "parent_title": "",
                "content": "这是一段测试内容，用于验证Milvus入库功能",
                "item_name": "测试主体",
                "dense_vector": [0.01] * 1024,
                "sparse_vector": {},
                "part": 1,
            },
        ],
    )
    result = index_chunks(state)
    logger.info("✅ 测试6 index_service 通过，Milvus 入库成功")


# ============================================================
# 测试 7：knowledge_persist_service — MongoDB 持久化（需要 MongoDB）
# ============================================================
def test_07_knowledge_persist_service():
    from app.rag.import_.knowledge_persist_service import persist_knowledge

    state = create_default_state(
        file_title="测试文档_集成测试",
        item_name="测试主体",
        chunks=[{"content": "test"}],
        md_content="测试内容",
    )
    result = persist_knowledge(state)
    doc_id = result.get("knowledge_doc_id", "")
    logger.info(f"✅ 测试7 knowledge_persist_service 通过，doc_id={doc_id}")


# ============================================================
# 运行所有测试
# ============================================================
if __name__ == "__main__":
    tests = [
        ("entry_service", test_01_entry_service),
        ("doc_meta_service", test_02_doc_meta_service),
        ("split_service", test_03_split_service),
        ("item_name_service", test_04_item_name_service),
        ("embedding_service", test_05_embedding_service),
        ("index_service", test_06_index_service),
        ("knowledge_persist_service", test_07_knowledge_persist_service),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"开始测试: {name}")
            logger.info(f"{'='*50}")
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            logger.error(f"❌ {name} 测试失败: {e}")

    logger.info(f"\n{'='*50}")
    logger.info(f"测试结果: 通过 {passed} / 失败 {failed} / 总计 {len(tests)}")
    logger.info(f"{'='*50}")
