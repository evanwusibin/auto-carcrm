# -*- coding: utf-8 -*-
"""
结构化查询单元测试
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeStructuredQuery:
    """测试结构化查询节点"""

    def test_query_with_vehicle_info(self):
        """测试车辆信息查询"""
        from app.process.query.agent.nodes.node_structured_query import node_structured_query

        state = {
            "session_id": "test-001",
            "rewritten_query": "我的T5还在保修期内吗？",
            "extracted_entities": {
                "vehicle_model": "T5",
                "vin": "LVSHFFAN5MF123456",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_structured_query.query_structured_data") as mock_query:
            mock_query.return_value = {
                **state,
                "structured_chunks": [
                    {"chunk_id": "vehicle_001", "content": "车辆信息：T5...", "type": "vehicle_info", "score": 1.0},
                ],
            }
            result = node_structured_query(state)

            assert "structured_chunks" in result
            assert len(result["structured_chunks"]) > 0

    def test_query_with_maintenance_records(self):
        """测试保养记录查询"""
        from app.process.query.agent.nodes.node_structured_query import node_structured_query

        state = {
            "session_id": "test-002",
            "rewritten_query": "上次保养是什么时候？",
            "extracted_entities": {
                "vehicle_model": "T5",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_structured_query.query_structured_data") as mock_query:
            mock_query.return_value = {
                **state,
                "structured_chunks": [
                    {"chunk_id": "maintenance_001", "content": "保养记录：2024-01-01...", "type": "maintenance_record", "score": 0.9},
                ],
            }
            result = node_structured_query(state)

            assert result["structured_chunks"][0]["type"] == "maintenance_record"

    def test_query_with_empty_result(self):
        """测试无结果查询"""
        from app.process.query.agent.nodes.node_structured_query import node_structured_query

        state = {
            "session_id": "test-003",
            "rewritten_query": "不存在的问题",
            "extracted_entities": {},
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_structured_query.query_structured_data") as mock_query:
            mock_query.return_value = {
                **state,
                "structured_chunks": [],
            }
            result = node_structured_query(state)

            assert result["structured_chunks"] == []


class TestStructuredQueryService:
    """测试结构化查询服务"""

    def test_validate_structured_state_with_valid_input(self):
        """测试有效输入校验"""
        from app.rag.query.structured_query_service import validate_structured_state

        state = {
            "rewritten_query": "我的T5还在保修期内吗？",
        }

        result = validate_structured_state(state)
        assert result == "我的T5还在保修期内吗？"

    def test_validate_structured_state_with_empty_query(self):
        """测试空查询校验"""
        from app.rag.query.structured_query_service import validate_structured_state

        state = {
            "rewritten_query": "",
        }

        with pytest.raises(ValueError, match="rewritten_query 为空"):
            validate_structured_state(state)

    def test_query_vehicle_info(self):
        """测试车辆信息查询"""
        from app.rag.query.structured_query_service import query_vehicle_info

        entities = {
            "vehicle_model": "T5",
            "vin": "LVSHFFAN5MF123456",
        }

        result = query_vehicle_info(entities)
        assert isinstance(result, list)

    def test_query_maintenance_records(self):
        """测试保养记录查询"""
        from app.rag.query.structured_query_service import query_maintenance_records

        entities = {
            "vehicle_model": "T5",
        }

        result = query_maintenance_records(entities)
        assert isinstance(result, list)

    def test_query_warranty_policies(self):
        """测试质保规则查询"""
        from app.rag.query.structured_query_service import query_warranty_policies

        entities = {
            "vehicle_model": "T5",
        }

        result = query_warranty_policies(entities)
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
