# -*- coding: utf-8 -*-
"""
单元测试配置文件
pytest 会自动加载此文件中的 fixture
"""
import pytest
import sys
import os

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_state():
    """示例状态数据，用于测试"""
    return {
        "task_id": "test-001",
        "session_id": "sess-test-001",
        "original_query": "烫金机怎么用？",
        "rewritten_query": "烫金机的使用方法是什么？",
        "item_names": ["HAK 180 烫金机"],
        "is_stream": False,
    }


@pytest.fixture
def import_state():
    """导入流程状态数据"""
    return {
        "task_id": "test-import-001",
        "local_file_path": "test.pdf",
        "local_dir": "./output",
        "is_pdf_read_enabled": True,
        "is_md_read_enabled": False,
    }


@pytest.fixture
def query_state():
    """查询流程状态数据"""
    return {
        "session_id": "sess-test-001",
        "original_query": "烫金机怎么用？",
        "rewritten_query": "烫金机的使用方法是什么？",
        "item_names": ["HAK 180 烫金机"],
        "is_stream": False,
        "embedding_chunks": [],
        "hyde_embedding_chunks": [],
        "web_search_docs": [],
        "rrf_chunks": [],
        "reranked_docs": [],
        "answer": "",
        "image_urls": [],
    }
