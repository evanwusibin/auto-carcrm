# -*- coding: utf-8 -*-
"""单元测试：entry_service — 文件类型识别与状态初始化"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.rag.import_.entry_service import resolve_input_file
from app.process.import_.agent.state import create_default_state


def test_md_file():
    """测试：识别 .md 文件"""
    state = create_default_state(local_file_path="D:/docs/保养手册.md")
    result = resolve_input_file(state)
    assert result["is_md_read_enabled"] == True
    assert result["is_pdf_read_enabled"] == False
    assert result["md_path"] == "D:/docs/保养手册.md"
    assert result["file_title"] == "保养手册"
    print("✅ test_md_file 通过")


def test_pdf_file():
    """测试：识别 .pdf 文件"""
    state = create_default_state(local_file_path="D:/docs/维修手册.pdf")
    result = resolve_input_file(state)
    assert result["is_pdf_read_enabled"] == True
    assert result["is_md_read_enabled"] == False
    assert result["pdf_path"] == "D:/docs/维修手册.pdf"
    assert result["file_title"] == "维修手册"
    print("✅ test_pdf_file 通过")


def test_empty_path():
    """测试：空路径应抛出 ValueError"""
    state = create_default_state(local_file_path="")
    try:
        resolve_input_file(state)
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "local_file_path为空" in str(e)
        print("✅ test_empty_path 通过")


def test_unsupported_type():
    """测试：不支持的文件类型应抛出 ValueError"""
    state = create_default_state(local_file_path="D:/docs/数据.xlsx")
    try:
        resolve_input_file(state)
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "不支持的文件类型" in str(e)
        print("✅ test_unsupported_type 通过")


# ==================== doc_meta_service 测试 ====================
from app.rag.import_.doc_meta_service import (
    extract_vehicle_model, extract_version, extract_dates, extract_doc_type, extract_doc_meta
)


def test_extract_vehicle_model():
    """测试：从标题中抽取车型"""
    assert extract_vehicle_model("HAK180使用说明书", "") == "HAK180"
    assert extract_vehicle_model("HK-180 维修手册", "") == "HK-180"
    assert extract_vehicle_model("无车型标题", "") == ""
    print("✅ test_extract_vehicle_model 通过")


def test_extract_version():
    """测试：从标题中抽取版本号"""
    assert extract_version("保养手册V2.1", "") == "V2.1"
    assert extract_version("维修手册v1.0", "") == "v1.0"
    assert extract_version("无版本标题", "") == ""
    print("✅ test_extract_version 通过")


def test_extract_dates():
    """测试：从内容中抽取日期"""
    content = "生效日期：2024-01-01，有效期至2025-12-31"
    effective, expiry = extract_dates(content)
    assert "2024" in effective
    assert "2025" in expiry
    print("✅ test_extract_dates 通过")


def test_extract_doc_type():
    """测试：判断文档类型"""
    assert extract_doc_type("T5轻卡保养手册", "") == "保养手册"
    assert extract_doc_type("质保政策说明", "") == "质保政策"
    assert extract_doc_type("DC-DC故障案例分析", "") == "故障案例"
    assert extract_doc_type("随机文档", "") == "其他"
    print("✅ test_extract_doc_type 通过")


def test_extract_doc_meta():
    """测试：元数据抽取主入口"""
    state = create_default_state(
        file_title="HAK180保养手册V2.1",
        md_content="生效日期：2024-01-01，本手册适用于HAK180车型的定期保养",
    )
    result = extract_doc_meta(state)
    assert result["vehicle_model"] == "HAK180"
    assert result["doc_version"] == "V2.1"
    assert result["doc_type"] == "保养手册"
    assert "2024" in result["effective_date"]
    print("✅ test_extract_doc_meta 通过")


# ==================== split_service 测试 ====================
from app.rag.import_.split_service import split_by_titles


def test_split_by_titles():
    """测试：按标题切分文档"""
    content = """# 第一章 保养概述

本章介绍保养的基本概念。

## 1.1 保养周期

建议每5000公里保养一次。

# 第二章 维修指南

本章介绍常见故障的维修方法。

## 2.1 电池故障

电池故障的排查步骤。"""
    chunks = split_by_titles(content, "测试手册")
    assert len(chunks) >= 2
    assert chunks[0]["file_title"] == "测试手册"
    print(f"✅ test_split_by_titles 通过，切出 {len(chunks)} 块")


def test_split_no_title():
    """测试：无标题文档"""
    content = "这是一段没有标题的纯文本内容，用于测试默认切分逻辑。"
    chunks = split_by_titles(content, "无标题文档")
    assert len(chunks) >= 1
    assert chunks[0]["title"] == "default"
    print("✅ test_split_no_title 通过")


# ==================== item_name_service 测试 ====================
from app.rag.import_.item_name_service import validate_chunks_and_title, build_document_context


def test_validate_chunks_and_title():
    """测试：校验chunks和标题"""
    state = {
        "chunks": [
            {"file_title": "保养手册", "title": "# 概述", "content": "保养概述内容"},
            {"file_title": "保养手册", "title": "# 周期", "content": "保养周期内容"},
        ],
        "file_title": "保养手册",
    }
    chunks, title = validate_chunks_and_title(state)
    assert len(chunks) == 2
    assert title == "保养手册"
    print("✅ test_validate_chunks_and_title 通过")


def test_validate_chunks_empty():
    """测试：空chunks应抛出异常"""
    state = {"chunks": [], "file_title": "测试"}
    try:
        validate_chunks_and_title(state)
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "chunks" in str(e)
        print("✅ test_validate_chunks_empty 通过")


def test_build_document_context():
    """测试：上下文拼接"""
    chunks = [
        {"title": "# 标题1", "parent_title": "", "content": "内容1"},
        {"title": "# 标题2", "parent_title": "", "content": "内容2"},
        {"title": "# 标题3", "parent_title": "", "content": "内容3"},
    ]
    context = build_document_context(chunks)
    assert "标题1" in context
    assert "内容1" in context
    print("✅ test_build_document_context 通过")


# ==================== embedding_service 测试 ====================
from app.rag.import_.embedding_service import require_chunks


def test_require_chunks():
    """测试：校验chunks非空"""
    state = {"chunks": [{"content": "test"}]}
    result = require_chunks(state)
    assert len(result) == 1
    print("✅ test_require_chunks 通过")


def test_require_chunks_empty():
    """测试：空chunks应抛出异常"""
    state = {"chunks": []}
    try:
        require_chunks(state)
        assert False, "应该抛出 ValueError"
    except ValueError:
        print("✅ test_require_chunks_empty 通过")


# ==================== index_service 测试 ====================
from app.rag.import_.index_service import validate_chunks_index


def test_validate_chunks_index():
    """测试：校验chunks非空"""
    state = {"chunks": [{"content": "test", "dense_vector": [0.1]*1024}]}
    result = validate_chunks_index(state)
    assert len(result) == 1
    print("✅ test_validate_chunks_index 通过")


def test_validate_chunks_index_empty():
    """测试：空chunks应抛出异常"""
    state = {"chunks": []}
    try:
        validate_chunks_index(state)
        assert False, "应该抛出 ValueError"
    except ValueError:
        print("✅ test_validate_chunks_index_empty 通过")


if __name__ == "__main__":
    # entry_service 测试
    test_md_file()
    test_pdf_file()
    test_empty_path()
    test_unsupported_type()
    print("\n🎉 entry_service 所有测试通过！")

    # doc_meta_service 测试
    test_extract_vehicle_model()
    test_extract_version()
    test_extract_dates()
    test_extract_doc_type()
    test_extract_doc_meta()
    print("\n🎉 doc_meta_service 所有测试通过！")

    # split_service 测试
    test_split_by_titles()
    test_split_no_title()
    print("\n🎉 split_service 所有测试通过！")

    # item_name_service 测试
    test_validate_chunks_and_title()
    test_validate_chunks_empty()
    test_build_document_context()
    print("\n🎉 item_name_service 所有测试通过！")

    # embedding_service 测试
    test_require_chunks()
    test_require_chunks_empty()
    print("\n🎉 embedding_service 所有测试通过！")

    # index_service 测试
    test_validate_chunks_index()
    test_validate_chunks_index_empty()
    print("\n🎉 index_service 所有测试通过！")
