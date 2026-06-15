# -*- coding: utf-8 -*-
"""
案例检索单元测试（车辆相关测试数据）
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeCaseSearch:
    """测试案例检索节点"""

    def test_search_with_engine_noise(self):
        """测试发动机异响案例检索"""
        from app.process.query.agent.nodes.node_case_search import node_case_search

        state = {
            "session_id": "test-001",
            "rewritten_query": "发动机异响怎么修？",
            "extracted_entities": {
                "fault_symptom": "发动机异响",
                "vehicle_model": "T5",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_case_search.search_cases") as mock_search:
            mock_search.return_value = {
                **state,
                "case_chunks": [
                    {"chunk_id": "case-001", "content": "案例：T5发动机异响，原因：皮带松弛，方案：更换皮带", "score": 0.95},
                ],
            }
            result = node_case_search(state)

            assert "发动机异响" in result["case_chunks"][0]["content"]

    def test_search_with_battery_issue(self):
        """测试电池故障案例检索"""
        from app.process.query.agent.nodes.node_case_search import node_case_search

        state = {
            "session_id": "test-002",
            "rewritten_query": "电池续航下降怎么办？",
            "extracted_entities": {
                "fault_symptom": "电池续航下降",
                "vehicle_model": "T7",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_case_search.search_cases") as mock_search:
            mock_search.return_value = {
                **state,
                "case_chunks": [
                    {"chunk_id": "case-002", "content": "案例：T7电池续航下降，原因：电池老化，方案：更换电池", "score": 0.88},
                ],
            }
            result = node_case_search(state)

            assert "电池" in result["case_chunks"][0]["content"]

    def test_search_with_brake_issue(self):
        """测试刹车故障案例检索"""
        from app.process.query.agent.nodes.node_case_search import node_case_search

        state = {
            "session_id": "test-003",
            "rewritten_query": "刹车失灵怎么办？",
            "extracted_entities": {
                "fault_symptom": "刹车失灵",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_case_search.search_cases") as mock_search:
            mock_search.return_value = {
                **state,
                "case_chunks": [
                    {"chunk_id": "case-003", "content": "案例：刹车失灵，原因：刹车片磨损，方案：更换刹车片", "score": 0.82},
                ],
            }
            result = node_case_search(state)

            assert "刹车" in result["case_chunks"][0]["content"]

    def test_search_with_empty_result(self):
        """测试无结果检索"""
        from app.process.query.agent.nodes.node_case_search import node_case_search

        state = {
            "session_id": "test-004",
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
