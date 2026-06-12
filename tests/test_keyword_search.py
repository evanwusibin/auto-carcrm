# -*- coding: utf-8 -*-
"""
关键词检索单元测试
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeKeywordSearch:
    """测试关键词检索节点"""

    def test_search_with_fault_code(self):
        """测试故障码检索"""
        from app.process.query.agent.nodes.node_keyword_search import node_keyword_search

        state = {
            "session_id": "test-001",
            "rewritten_query": "P0A0F故障码是什么意思？",
            "extracted_entities": {
                "fault_codes": "P0A0F",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_keyword_search.search_by_keywords") as mock_search:
            mock_search.return_value = {
                **state,
                "keyword_chunks": [
                    {"chunk_id": "chunk-001", "content": "P0A0F故障码解释...", "score": 0.95},
                ],
            }
            result = node_keyword_search(state)

            assert "keyword_chunks" in result
            assert len(result["keyword_chunks"]) > 0

    def test_search_with_vehicle_model(self):
        """测试车型检索"""
        from app.process.query.agent.nodes.node_keyword_search import node_keyword_search

        state = {
            "session_id": "test-002",
            "rewritten_query": "T5保养周期是多久？",
            "extracted_entities": {
                "vehicle_model": "T5",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_keyword_search.search_by_keywords") as mock_search:
            mock_search.return_value = {
                **state,
                "keyword_chunks": [
                    {"chunk_id": "chunk-002", "content": "T5保养周期...", "score": 0.88},
                ],
            }
            result = node_keyword_search(state)

            assert result["keyword_chunks"][0]["content"] == "T5保养周期..."

    def test_search_with_empty_result(self):
        """测试无结果检索"""
        from app.process.query.agent.nodes.node_keyword_search import node_keyword_search

        state = {
            "session_id": "test-003",
            "rewritten_query": "不存在的问题",
            "extracted_entities": {},
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_keyword_search.search_by_keywords") as mock_search:
            mock_search.return_value = {
                **state,
                "keyword_chunks": [],
            }
            result = node_keyword_search(state)

            assert result["keyword_chunks"] == []


class TestKeywordSearchService:
    """测试关键词检索服务"""

    def test_validate_keyword_state_with_valid_input(self):
        """测试有效输入校验"""
        from app.rag.query.keyword_search_service import validate_keyword_state

        state = {
            "rewritten_query": "P0A0F故障码是什么意思？",
        }

        result = validate_keyword_state(state)
        assert result == "P0A0F故障码是什么意思？"

    def test_validate_keyword_state_with_empty_query(self):
        """测试空查询校验"""
        from app.rag.query.keyword_search_service import validate_keyword_state

        state = {
            "rewritten_query": "",
        }

        with pytest.raises(ValueError, match="rewritten_query 为空"):
            validate_keyword_state(state)

    def test_tokenize_chinese(self):
        """测试中文分词"""
        from app.rag.query.keyword_search_service import tokenize_chinese

        # 测试中文分词
        tokens = tokenize_chinese("P0A0F故障码是什么意思？")
        assert "P" in tokens  # 简单分割模式下，P0A0F会被拆成单字符
        assert "故" in tokens  # 简单分割模式下，中文会被拆成单字符

    def test_extract_keywords_from_entities(self):
        """测试从实体中提取关键词"""
        from app.rag.query.keyword_search_service import extract_keywords_from_entities

        entities = {
            "vehicle_model": "T5",
            "fault_codes": "P0A0F",
            "component": "发动机",
        }

        keywords = extract_keywords_from_entities(entities)
        assert "T5" in keywords
        assert "P0A0F" in keywords
        assert "发动机" in keywords

    def test_extract_keywords_from_empty_entities(self):
        """测试从空实体中提取关键词"""
        from app.rag.query.keyword_search_service import extract_keywords_from_entities

        entities = {}
        keywords = extract_keywords_from_entities(entities)
        assert keywords == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
