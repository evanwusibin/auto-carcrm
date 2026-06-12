# -*- coding: utf-8 -*-
"""
导入流程单元测试
根据实际代码结构调整，测试每个节点的核心逻辑
"""
import pytest
from unittest.mock import patch, MagicMock


class TestNodeEntry:
    """测试入口节点"""

    def test_node_entry_with_pdf(self, tmp_path):
        """测试PDF文件识别"""
        # 创建临时PDF文件
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        state = {
            "task_id": "test-001",
            "local_file_path": str(pdf_file),
            "local_dir": str(tmp_path),
        }

        from app.process.import_.agent.nodes.node_entry import node_entry

        with patch("app.process.import_.agent.nodes.node_entry.resolve_input_file") as mock_resolve:
            mock_resolve.return_value = {
                **state,
                "is_pdf_read_enabled": True,
                "is_md_read_enabled": False,
                "file_title": "test",
                "pdf_path": str(pdf_file),
            }
            result = node_entry(state)

            assert result.get("is_pdf_read_enabled") == True
            assert result.get("is_md_read_enabled") == False
            assert result.get("file_title") == "test"

    def test_node_entry_with_md(self, tmp_path):
        """测试MD文件识别"""
        md_file = tmp_path / "test.md"
        md_file.write_text("# 测试标题\n测试内容")

        state = {
            "task_id": "test-002",
            "local_file_path": str(md_file),
            "local_dir": str(tmp_path),
        }

        from app.process.import_.agent.nodes.node_entry import node_entry

        with patch("app.process.import_.agent.nodes.node_entry.resolve_input_file") as mock_resolve:
            mock_resolve.return_value = {
                **state,
                "is_pdf_read_enabled": False,
                "is_md_read_enabled": True,
                "file_title": "test",
                "md_path": str(md_file),
            }
            result = node_entry(state)

            assert result.get("is_md_read_enabled") == True
            assert result.get("is_pdf_read_enabled") == False


class TestNodePdfToMd:
    """测试PDF转MD节点"""

    def test_pdf_conversion(self):
        """测试PDF转换"""
        state = {
            "task_id": "test-001",
            "pdf_path": "./test.pdf",
            "local_dir": "./output",
        }

        from app.process.import_.agent.nodes.node_pdf_to_md import node_pdf_to_md

        with patch("app.process.import_.agent.nodes.node_pdf_to_md.parse_pdf_to_markdown") as mock_parse:
            mock_parse.return_value = {
                **state,
                "md_path": "./output/test.md",
                "md_content": "# 测试标题\n测试内容",
            }
            result = node_pdf_to_md(state)

            assert "md_path" in result
            assert "md_content" in result
            assert result["md_content"] == "# 测试标题\n测试内容"


class TestNodeDocumentSplit:
    """测试文档切分节点"""

    def test_document_split(self):
        """测试文档切分"""
        state = {
            "task_id": "test-001",
            "md_content": "# 标题1\n内容1\n\n# 标题2\n内容2",
            "md_path": "./test.md",
            "file_title": "测试文档",
        }

        from app.process.import_.agent.nodes.node_document_split import node_document_split

        with patch("app.process.import_.agent.nodes.node_document_split.split_document") as mock_split:
            mock_split.return_value = {
                **state,
                "chunks": [
                    {"chunk_id": "chunk-001", "content": "标题1\n内容1", "title": "标题1"},
                    {"chunk_id": "chunk-002", "content": "标题2\n内容2", "title": "标题2"},
                ],
            }
            result = node_document_split(state)

            assert "chunks" in result
            assert len(result["chunks"]) == 2

    def test_empty_content(self):
        """测试空内容处理"""
        state = {
            "task_id": "test-002",
            "md_content": "",
            "md_path": "./test.md",
            "file_title": "测试文档",
        }

        from app.process.import_.agent.nodes.node_document_split import node_document_split

        with patch("app.process.import_.agent.nodes.node_document_split.split_document") as mock_split:
            mock_split.return_value = {
                **state,
                "chunks": [],
            }
            result = node_document_split(state)

            assert "chunks" in result
            assert len(result["chunks"]) == 0


class TestNodeBgeEmbedding:
    """测试向量化节点"""

    def test_embedding_generation(self):
        """测试向量生成"""
        state = {
            "task_id": "test-001",
            "chunks": [
                {"chunk_id": "chunk-001", "content": "测试内容", "title": "测试标题"},
            ],
        }

        from app.process.import_.agent.nodes.node_bge_embedding import node_bge_embedding

        with patch("app.process.import_.agent.nodes.node_bge_embedding.generate_chunk_embeddings") as mock_embed:
            mock_embed.return_value = {
                **state,
                "chunks": [
                    {
                        "chunk_id": "chunk-001",
                        "content": "测试内容",
                        "title": "测试标题",
                        "dense_vector": [0.1] * 1024,
                        "sparse_vector": {1: 0.5, 2: 0.3},
                    }
                ],
            }
            result = node_bge_embedding(state)

            assert "chunks" in result
            assert "dense_vector" in result["chunks"][0]
            assert "sparse_vector" in result["chunks"][0]
            assert len(result["chunks"][0]["dense_vector"]) == 1024


class TestNodeImportMilvus:
    """测试Milvus入库节点"""

    def test_import_to_milvus(self):
        """测试入库Milvus"""
        state = {
            "task_id": "test-001",
            "chunks": [
                {
                    "chunk_id": "chunk-001",
                    "content": "测试内容",
                    "title": "测试标题",
                    "dense_vector": [0.1] * 1024,
                    "sparse_vector": {1: 0.5, 2: 0.3},
                }
            ],
            "item_name": "HAK 180 烫金机",
        }

        from app.process.import_.agent.nodes.node_import_milvus import node_import_milvus

        with patch("app.process.import_.agent.nodes.node_import_milvus.index_chunks") as mock_index:
            mock_index.return_value = state
            result = node_import_milvus(state)

            assert result is not None
            assert "chunks" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
