# -*- coding: utf-8 -*-
"""
查询流程单元测试
根据实际代码结构调整，测试每个节点的核心逻辑
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeItemNameConfirm:
    """测试意图识别与主体确认节点"""

    def test_item_name_confirm_with_valid_input(self):
        """测试有效输入的主体确认"""
        state = {
            "session_id": "sess-test-001",
            "is_stream": False,
            "original_query": "烫金机怎么用？",
        }

        from app.process.query.agent.nodes.node_item_name_confirm import node_item_name_confirm

        with patch("app.process.query.agent.nodes.node_item_name_confirm.confirm_item_name") as mock_confirm:
            mock_confirm.return_value = {
                **state,
                "item_names": ["HAK 180 烫金机"],
                "rewritten_query": "烫金机的使用方法是什么？",
            }
            result = node_item_name_confirm(state)

            assert "item_names" in result
            assert "rewritten_query" in result
            assert result["item_names"] == ["HAK 180 烫金机"]

    def test_item_name_confirm_with_no_match(self):
        """测试无匹配的主体确认"""
        state = {
            "session_id": "sess-test-002",
            "is_stream": False,
            "original_query": "今天天气怎么样？",
        }

        from app.process.query.agent.nodes.node_item_name_confirm import node_item_name_confirm

        with patch("app.process.query.agent.nodes.node_item_name_confirm.confirm_item_name") as mock_confirm:
            mock_confirm.return_value = {
                **state,
                "item_names": [],
                "rewritten_query": "今天天气怎么样？",
                "answer": "抱歉，我只能回答商用车售后相关问题。",
            }
            result = node_item_name_confirm(state)

            assert "answer" in result
            assert result.get("item_names") == []


class TestNodeSearchEmbedding:
    """测试向量检索节点"""

    def test_search_embedding(self):
        """测试向量检索"""
        state = {
            "session_id": "sess-test-001",
            "is_stream": False,
            "rewritten_query": "烫金机的使用方法是什么？",
            "item_names": ["HAK 180 烫金机"],
        }

        from app.process.query.agent.nodes.node_search_embedding import node_search_embedding

        with patch("app.process.query.agent.nodes.node_search_embedding.search_by_embedding") as mock_search:
            mock_search.return_value = {
                **state,
                "embedding_chunks": [
                    {"chunk_id": "chunk-001", "content": "使用方法...", "score": 0.85},
                    {"chunk_id": "chunk-002", "content": "注意事项...", "score": 0.72},
                ],
            }
            result = node_search_embedding(state)

            assert "embedding_chunks" in result
            assert len(result["embedding_chunks"]) > 0
            assert result["embedding_chunks"][0]["score"] == 0.85


class TestNodeRrf:
    """测试RRF融合节点"""

    def test_rrf_fusion(self):
        """测试RRF融合"""
        state = {
            "session_id": "sess-test-001",
            "is_stream": False,
            "embedding_chunks": [
                {"chunk_id": "chunk-001", "content": "内容1", "score": 0.85},
                {"chunk_id": "chunk-002", "content": "内容2", "score": 0.72},
            ],
            "hyde_embedding_chunks": [
                {"chunk_id": "chunk-001", "content": "内容1", "score": 0.80},
                {"chunk_id": "chunk-003", "content": "内容3", "score": 0.65},
            ],
        }

        from app.process.query.agent.nodes.node_rrf import node_rrf

        with patch("app.process.query.agent.nodes.node_rrf.fuse_by_rrf") as mock_rrf:
            mock_rrf.return_value = {
                **state,
                "rrf_chunks": [
                    {"chunk_id": "chunk-001", "content": "内容1", "score": 0.95},
                    {"chunk_id": "chunk-002", "content": "内容2", "score": 0.72},
                    {"chunk_id": "chunk-003", "content": "内容3", "score": 0.65},
                ],
            }
            result = node_rrf(state)

            assert "rrf_chunks" in result
            assert len(result["rrf_chunks"]) == 3


class TestNodeRerank:
    """测试重排序节点"""

    def test_rerank(self):
        """测试重排序"""
        state = {
            "session_id": "sess-test-001",
            "is_stream": False,
            "rewritten_query": "烫金机的使用方法是什么？",
            "rrf_chunks": [
                {"chunk_id": "chunk-001", "content": "内容1", "score": 0.95},
                {"chunk_id": "chunk-002", "content": "内容2", "score": 0.72},
            ],
            "web_search_docs": [],
        }

        from app.process.query.agent.nodes.node_rerank import node_rerank

        with patch("app.process.query.agent.nodes.node_rerank.rerank_documents") as mock_rerank:
            mock_rerank.return_value = {
                **state,
                "reranked_docs": [
                    {"chunk_id": "chunk-001", "content": "内容1", "score": 0.98},
                    {"chunk_id": "chunk-002", "content": "内容2", "score": 0.75},
                ],
            }
            result = node_rerank(state)

            assert "reranked_docs" in result
            assert result["reranked_docs"][0]["score"] == 0.98


class TestNodeAnswerOutput:
    """测试答案生成节点"""

    def test_answer_generation(self):
        """测试答案生成"""
        state = {
            "session_id": "sess-test-001",
            "is_stream": False,
            "rewritten_query": "烫金机的使用方法是什么？",
            "reranked_docs": [
                {"chunk_id": "chunk-001", "content": "使用方法：1.开机...", "score": 0.98},
            ],
            "item_names": ["HAK 180 烫金机"],
            "history": [],
            "is_stream": False,
        }

        from app.process.query.agent.nodes.node_answer_output import node_answer_output

        with patch("app.process.query.agent.nodes.node_answer_output.generate_answer") as mock_generate:
            mock_generate.return_value = {
                **state,
                "answer": "烫金机的使用方法：1.开机预热...",
                "image_urls": [],
            }
            result = node_answer_output(state)

            assert "answer" in result
            assert len(result["answer"]) > 0

    def test_answer_with_images(self):
        """测试带图片的答案生成"""
        state = {
            "session_id": "sess-test-002",
            "is_stream": False,
            "rewritten_query": "烫金机的外观是什么样的？",
            "reranked_docs": [
                {"chunk_id": "chunk-001", "content": "外观如图...", "score": 0.95, "url": "http://example.com/img.jpg"},
            ],
            "item_names": ["HAK 180 烫金机"],
            "history": [],
            "is_stream": False,
        }

        from app.process.query.agent.nodes.node_answer_output import node_answer_output

        with patch("app.process.query.agent.nodes.node_answer_output.generate_answer") as mock_generate:
            mock_generate.return_value = {
                **state,
                "answer": "烫金机的外观如图所示...",
                "image_urls": ["http://example.com/img.jpg"],
            }
            result = node_answer_output(state)

            assert "answer" in result
            assert "image_urls" in result
            assert len(result["image_urls"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
