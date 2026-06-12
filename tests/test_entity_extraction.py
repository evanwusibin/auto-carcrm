# -*- coding: utf-8 -*-
"""
实体抽取节点单元测试
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeEntityExtraction:
    """测试实体抽取节点"""

    def test_extract_vehicle_model_and_symptom(self):
        """测试车型和故障现象抽取"""
        from app.process.query.agent.nodes.node_entity_extraction import node_entity_extraction

        state = {
            "session_id": "test-001",
            "rewritten_query": "T5车型发动机异响怎么办？",
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_entity_extraction.extract_entities") as mock_extract:
            mock_extract.return_value = {
                **state,
                "extracted_entities": {
                    "vehicle_model": "T5",
                    "fault_symptom": "发动机异响",
                },
            }
            result = node_entity_extraction(state)

            assert "extracted_entities" in result
            assert result["extracted_entities"]["vehicle_model"] == "T5"
            assert result["extracted_entities"]["fault_symptom"] == "发动机异响"

    def test_extract_vin_and_fault_code(self):
        """测试VIN码和故障码抽取"""
        from app.process.query.agent.nodes.node_entity_extraction import node_entity_extraction

        state = {
            "session_id": "test-002",
            "rewritten_query": "车架号LVSHFFAN5MF123456报故障码P0A0F",
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_entity_extraction.extract_entities") as mock_extract:
            mock_extract.return_value = {
                **state,
                "extracted_entities": {
                    "vin": "LVSHFFAN5MF123456",
                    "fault_codes": "P0A0F",
                },
            }
            result = node_entity_extraction(state)

            assert result["extracted_entities"]["vin"] == "LVSHFFAN5MF123456"
            assert result["extracted_entities"]["fault_codes"] == "P0A0F"

    def test_extract_mileage(self):
        """测试里程抽取"""
        from app.process.query.agent.nodes.node_entity_extraction import node_entity_extraction

        state = {
            "session_id": "test-003",
            "rewritten_query": "我的车开了5万公里，需要保养吗？",
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_entity_extraction.extract_entities") as mock_extract:
            mock_extract.return_value = {
                **state,
                "extracted_entities": {
                    "mileage": "50000",
                },
            }
            result = node_entity_extraction(state)

            assert result["extracted_entities"]["mileage"] == "50000"

    def test_extract_empty_entities(self):
        """测试无实体抽取"""
        from app.process.query.agent.nodes.node_entity_extraction import node_entity_extraction

        state = {
            "session_id": "test-004",
            "rewritten_query": "你好",
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_entity_extraction.extract_entities") as mock_extract:
            mock_extract.return_value = {
                **state,
                "extracted_entities": {},
            }
            result = node_entity_extraction(state)

            assert result["extracted_entities"] == {}


class TestEntityExtractionService:
    """测试实体抽取服务"""

    def test_validate_entity_state_with_valid_input(self):
        """测试有效输入校验"""
        from app.rag.query.entity_extraction_service import validate_entity_state

        state = {
            "rewritten_query": "T5车型发动机异响怎么办？",
        }

        result = validate_entity_state(state)
        assert result == "T5车型发动机异响怎么办？"

    def test_validate_entity_state_with_empty_query(self):
        """测试空查询校验"""
        from app.rag.query.entity_extraction_service import validate_entity_state

        state = {
            "rewritten_query": "",
        }

        with pytest.raises(ValueError, match="rewritten_query 为空"):
            validate_entity_state(state)

    def test_entity_types_mapping(self):
        """测试实体类型映射"""
        from app.rag.query.entity_extraction_service import ENTITY_TYPES

        assert "vehicle_model" in ENTITY_TYPES
        assert "vin" in ENTITY_TYPES
        assert "fault_codes" in ENTITY_TYPES
        assert "mileage" in ENTITY_TYPES
        assert "component" in ENTITY_TYPES
        assert "purchase_date" in ENTITY_TYPES
        assert "fault_symptom" in ENTITY_TYPES
        assert len(ENTITY_TYPES) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
