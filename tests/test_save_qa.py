# -*- coding: utf-8 -*-
"""
QA保存单元测试
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeSaveQa:
    """测试QA保存节点"""

    def test_save_qa_with_full_data(self):
        """测试完整数据保存"""
        from app.process.query.agent.nodes.node_save_qa import node_save_qa

        state = {
            "session_id": "test-001",
            "original_query": "发动机异响怎么修？",
            "answer": "发动机异响可能是由于...",
            "image_urls": ["http://example.com/img.jpg"],
            "references": [
                {"chunk_id": "chunk-001", "title": "维修手册", "source": "知识库"},
            ],
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_save_qa.save_qa_session") as mock_save:
            mock_save.return_value = None
            result = node_save_qa(state)

            assert result is not None
            mock_save.assert_called_once()

    def test_save_qa_with_minimal_data(self):
        """测试最小数据保存"""
        from app.process.query.agent.nodes.node_save_qa import node_save_qa

        state = {
            "session_id": "test-002",
            "original_query": "你好",
            "answer": "你好！有什么可以帮您的吗？",
            "is_stream": False,
        }

        with patch("app.process.query.agent.nodes.node_save_qa.save_qa_session") as mock_save:
            mock_save.return_value = None
            result = node_save_qa(state)

            assert result is not None


class TestQaPersistService:
    """测试QA持久化服务"""

    def test_validate_qa_state_with_valid_input(self):
        """测试有效输入校验"""
        from app.rag.query.qa_persist_service import validate_qa_state

        state = {
            "session_id": "test-001",
            "original_query": "发动机异响怎么修？",
            "answer": "发动机异响可能是由于...",
        }

        session_id, original_query, answer = validate_qa_state(state)
        assert session_id == "test-001"
        assert original_query == "发动机异响怎么修？"
        assert answer == "发动机异响可能是由于..."

    def test_validate_qa_state_with_empty_session_id(self):
        """测试空session_id校验"""
        from app.rag.query.qa_persist_service import validate_qa_state

        state = {
            "session_id": "",
            "original_query": "发动机异响怎么修？",
            "answer": "发动机异响可能是由于...",
        }

        with pytest.raises(ValueError, match="session_id 为空"):
            validate_qa_state(state)

    def test_validate_qa_state_with_empty_query(self):
        """测试空query校验"""
        from app.rag.query.qa_persist_service import validate_qa_state

        state = {
            "session_id": "test-001",
            "original_query": "",
            "answer": "发动机异响可能是由于...",
        }

        with pytest.raises(ValueError, match="original_query 为空"):
            validate_qa_state(state)

    def test_validate_qa_state_with_empty_answer(self):
        """测试空answer校验"""
        from app.rag.query.qa_persist_service import validate_qa_state

        state = {
            "session_id": "test-001",
            "original_query": "发动机异响怎么修？",
            "answer": "",
        }

        with pytest.raises(ValueError, match="answer 为空"):
            validate_qa_state(state)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
