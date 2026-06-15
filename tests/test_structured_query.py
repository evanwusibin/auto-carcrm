# -*- coding: utf-8 -*-
"""
结构化查询单元测试（车辆相关测试数据）
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeStructuredQuery:
    """测试结构化查询节点"""

    def test_query_with_vehicle_info(self):
        """测试车辆信息查询（T5）"""
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
                    {"chunk_id": "vehicle_001", "content": "T5车辆信息：购买日期2024-01-01，里程50000公里", "type": "vehicle_info", "score": 1.0},
                ],
            }
            result = node_structured_query(state)

            assert "T5" in result["structured_chunks"][0]["content"]

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
                    {"chunk_id": "maintenance_001", "content": "保养记录：2024-06-01，里程45000公里，更换机油", "type": "maintenance_record", "score": 0.9},
                ],
            }
            result = node_structured_query(state)

            assert "保养记录" in result["structured_chunks"][0]["content"]

    def test_query_with_warranty_policy(self):
        """测试质保规则查询"""
        from app.process.query.agent.nodes.node_structured_query import node_structured_query

        state = {
            "session_id": "test-003",
            "rewritten_query": "发动机质保多久？",
            "extracted_entities": {
                "component": "发动机",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_structured_query.query_structured_data") as mock_query:
            mock_query.return_value = {
                **state,
                "structured_chunks": [
                    {"chunk_id": "warranty_001", "content": "质保规则：发动机质保3年或10万公里", "type": "warranty_policy", "score": 0.8},
                ],
            }
            result = node_structured_query(state)

            assert "发动机" in result["structured_chunks"][0]["content"]

    def test_query_with_empty_result(self):
        """测试无结果查询"""
        from app.process.query.agent.nodes.node_structured_query import node_structured_query

        state = {
            "session_id": "test-004",
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
            "component": "发动机",
        }

        result = query_warranty_policies(entities)
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
