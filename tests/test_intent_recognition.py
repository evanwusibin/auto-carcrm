# -*- coding: utf-8 -*-
"""
意图识别节点单元测试（车辆相关测试数据）
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeIntentRecognition:
    """测试意图识别节点"""

    def test_recognize_after_sales_intent(self):
        """测试售后服务意图识别（发动机异响）"""
        from app.process.query.agent.nodes.node_intent_recognition import node_intent_recognition

        state = {
            "session_id": "test-001",
            "rewritten_query": "我的T5发动机异响怎么办？",
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_intent_recognition.recognize_intent") as mock_recognize:
            mock_recognize.return_value = {
                **state,
                "intent": "after_sales_service",
            }
            result = node_intent_recognition(state)

            assert result["intent"] == "after_sales_service"

    def test_recognize_pre_sales_intent(self):
        """测试售前咨询意图识别（价格咨询）"""
        from app.process.query.agent.nodes.node_intent_recognition import node_intent_recognition

        state = {
            "session_id": "test-002",
            "rewritten_query": "T5商用车多少钱？",
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_intent_recognition.recognize_intent") as mock_recognize:
            mock_recognize.return_value = {
                **state,
                "intent": "pre_sales_consultation",
            }
            result = node_intent_recognition(state)

            assert result["intent"] == "pre_sales_consultation"

    def test_recognize_vehicle_usage_intent(self):
        """测试用车指导意图识别（空调使用）"""
        from app.process.query.agent.nodes.node_intent_recognition import node_intent_recognition

        state = {
            "session_id": "test-003",
            "rewritten_query": "T5空调怎么开？",
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_intent_recognition.recognize_intent") as mock_recognize:
            mock_recognize.return_value = {
                **state,
                "intent": "vehicle_usage_guide",
            }
            result = node_intent_recognition(state)

            assert result["intent"] == "vehicle_usage_guide"

    def test_recognize_warranty_intent(self):
        """测试质保查询意图识别"""
        from app.process.query.agent.nodes.node_intent_recognition import node_intent_recognition

        state = {
            "session_id": "test-004",
            "rewritten_query": "我的车还在保修期内吗？",
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_intent_recognition.recognize_intent") as mock_recognize:
            mock_recognize.return_value = {
                **state,
                "intent": "after_sales_service",
            }
            result = node_intent_recognition(state)

            assert result["intent"] == "after_sales_service"


class TestIntentRecognitionService:
    """测试意图识别服务"""

    def test_validate_intent_state_with_valid_input(self):
        """测试有效输入校验"""
        from app.rag.query.intent_recognition_service import validate_intent_state

        state = {
            "rewritten_query": "我的T5发动机异响怎么办？",
        }

        result = validate_intent_state(state)
        assert result == "我的T5发动机异响怎么办？"

    def test_validate_intent_state_with_empty_query(self):
        """测试空查询校验"""
        from app.rag.query.intent_recognition_service import validate_intent_state

        state = {
            "rewritten_query": "",
        }

        with pytest.raises(ValueError, match="rewritten_query 为空"):
            validate_intent_state(state)

    def test_intent_types_mapping(self):
        """测试意图类型映射"""
        from app.rag.query.intent_recognition_service import INTENT_TYPES

        assert "pre_sales_consultation" in INTENT_TYPES
        assert "after_sales_service" in INTENT_TYPES
        assert "vehicle_usage_guide" in INTENT_TYPES
        assert "complaint_emotion" in INTENT_TYPES
        assert "business_transaction" in INTENT_TYPES
        assert "general_chat" in INTENT_TYPES
        assert len(INTENT_TYPES) == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
