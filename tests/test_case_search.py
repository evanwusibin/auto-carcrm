# -*- coding: utf-8 -*-
"""
案例检索单元测试
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeCaseSearch:
    """测试案例检索节点"""

    def test_search_with_fault_symptom(self):
        """测试故障现象检索"""
        from app.process.query.agent.nodes.node_case_search import node_case_search

        state = {
            "session_id": "test-001",
            "rewritten_query": "发动机异响怎么修？",
            "extracted_entities": {
                "fault_symptom": "发动机异响",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_case_search.search_cases") as mock_search:
            mock_search.return_value = {
                **state,
                "case_chunks": [
                    {"chunk_id": "case-001", "content": "案例：发动机异响...", "score": 0.95},
                ],
            }
            result = node_case_search(state)

            assert "case_chunks" in result
            assert len(result["case_chunks"]) > 0

    def test_search_with_empty_result(self):
        """测试无结果检索"""
        from app.process.query.agent.nodes.node_case_search import node_case_search

        state = {
            "session_id": "test-002",
            "rewritten_query": "不存在的问题",
            "extracted_entities": {},
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_case_search.search_cases") as mock_search:
            mock_search.return_value = {
                **state,
                "case_chunks": [],
            }
            result = node_case_search(state)

            assert result["case_chunks"] == []


class TestCaseSearchService:
    """测试案例检索服务"""

    def test_validate_case_state_with_valid_input(self):
        """测试有效输入校验"""
        from app.rag.query.case_search_service import validate_case_state

        state = {
            "rewritten_query": "发动机异响怎么修？",
        }

        result = validate_case_state(state)
        assert result == "发动机异响怎么修？"

    def test_validate_case_state_with_empty_query(self):
        """测试空查询校验"""
        from app.rag.query.case_search_service import validate_case_state

        state = {
            "rewritten_query": "",
        }

        with pytest.raises(ValueError, match="rewritten_query 为空"):
            validate_case_state(state)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
