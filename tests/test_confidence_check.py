# -*- coding: utf-8 -*-
"""
置信度检查单元测试（车辆相关测试数据）
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeConfidenceCheck:
    """测试置信度检查节点"""

    def test_confidence_with_high_score(self):
        """测试高置信度（发动机异响）"""
        from app.process.query.agent.nodes.node_confidence_check import node_confidence_check

        state = {
            "session_id": "test-001",
            "rewritten_query": "发动机异响怎么修？",
            "reranked_docs": [
                {"chunk_id": "chunk-001", "content": "发动机异响可能是皮带松弛", "score": 0.95},
            ],
            "extracted_entities": {
                "fault_symptom": "发动机异响",
                "vehicle_model": "T5",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_confidence_check.check_confidence") as mock_check:
            mock_check.return_value = {
                **state,
                "confidence_score": 0.95,
                "need_followup": False,
                "followup_question": "",
            }
            result = node_confidence_check(state)

            assert result["confidence_score"] == 0.95
            assert result["need_followup"] == False

    def test_confidence_with_low_score_no_model(self):
        """测试低置信度且无车型（需要追问）"""
        from app.process.query.agent.nodes.node_confidence_check import node_confidence_check

        state = {
            "session_id": "test-002",
            "rewritten_query": "发动机异响怎么修？",
            "reranked_docs": [
                {"chunk_id": "chunk-001", "content": "发动机异响...", "score": 0.3},
            ],
            "extracted_entities": {},
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_confidence_check.check_confidence") as mock_check:
            mock_check.return_value = {
                **state,
                "confidence_score": 0.3,
                "need_followup": True,
                "followup_question": "请告诉我您的车型，以便我提供更准确的信息。",
            }
            result = node_confidence_check(state)

            assert result["confidence_score"] == 0.3
            assert result["need_followup"] == True
            assert "车型" in result["followup_question"]

    def test_confidence_with_low_score_no_symptom(self):
        """测试低置信度且无故障现象（需要追问）"""
        from app.process.query.agent.nodes.node_confidence_check import node_confidence_check

        state = {
            "session_id": "test-003",
            "rewritten_query": "我的车有问题",
            "reranked_docs": [
                {"chunk_id": "chunk-001", "content": "车辆故障...", "score": 0.4},
            ],
            "extracted_entities": {
                "vehicle_model": "T5",
            },
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_confidence_check.check_confidence") as mock_check:
            mock_check.return_value = {
                **state,
                "confidence_score": 0.4,
                "need_followup": True,
                "followup_question": "请描述一下具体的故障现象，以便我更好地帮助您。",
            }
            result = node_confidence_check(state)

            assert result["confidence_score"] == 0.4
            assert result["need_followup"] == True
            assert "故障现象" in result["followup_question"]


class TestConfidenceService:
    """测试置信度检查服务"""

    def test_validate_confidence_state_with_docs(self):
        """测试有文档的校验"""
        from app.rag.query.confidence_service import validate_confidence_state

        state = {
            "reranked_docs": [
                {"chunk_id": "chunk-001", "content": "发动机异响...", "score": 0.9},
            ],
        }

        result = validate_confidence_state(state)
        assert len(result) == 1

    def test_validate_confidence_state_with_empty_docs(self):
        """测试无文档的校验"""
        from app.rag.query.confidence_service import validate_confidence_state

        state = {
            "reranked_docs": [],
        }

        result = validate_confidence_state(state)
        assert result == []

    def test_calculate_confidence_score_with_docs(self):
        """测试有文档的置信度计算"""
        from app.rag.query.confidence_service import calculate_confidence_score

        docs = [
            {"chunk_id": "chunk-001", "content": "发动机异响...", "score": 0.95},
            {"chunk_id": "chunk-002", "content": "发动机异响...", "score": 0.85},
        ]

        score = calculate_confidence_score(docs)
        assert score == 0.95

    def test_calculate_confidence_score_with_empty_docs(self):
        """测试无文档的置信度计算"""
        from app.rag.query.confidence_service import calculate_confidence_score

        docs = []
        score = calculate_confidence_score(docs)
        assert score == 0.0

    def test_determine_followup_need_high_confidence(self):
        """测试高置信度不需要追问"""
        from app.rag.query.confidence_service import determine_followup_need

        need_followup, question = determine_followup_need(0.95, {"vehicle_model": "T5", "fault_symptom": "发动机异响"})
        assert need_followup == False
        assert question == ""

    def test_determine_followup_need_low_confidence_no_model(self):
        """测试低置信度且无车型需要追问"""
        from app.rag.query.confidence_service import determine_followup_need

        need_followup, question = determine_followup_need(0.3, {})
        assert need_followup == True
        assert "车型" in question

    def test_determine_followup_need_low_confidence_no_symptom(self):
        """测试低置信度且无故障现象需要追问"""
        from app.rag.query.confidence_service import determine_followup_need

        need_followup, question = determine_followup_need(0.4, {"vehicle_model": "T5"})
        assert need_followup == True
        assert "故障现象" in question


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
