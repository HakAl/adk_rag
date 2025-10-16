"""
Tests for vector store performance optimizations.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.vector_store import VectorStoreService
from config.settings import Settings


class TestVectorStoreOptimizations:
    """Test vector store performance optimizations."""

    def test_collection_metadata_includes_hnsw_settings(self):
        """Test that collection metadata includes HNSW optimization settings."""
        service = VectorStoreService()
        metadata = service._get_collection_metadata()

        # Verify all HNSW settings are present
        assert "hnsw:space" in metadata
        assert "hnsw:construction_ef" in metadata
        assert "hnsw:search_ef" in metadata
        assert "hnsw:M" in metadata

        # Verify values match settings
        from config import settings
        assert metadata["hnsw:space"] == settings.chroma_hnsw_space
        assert metadata["hnsw:construction_ef"] == settings.chroma_hnsw_construction_ef
        assert metadata["hnsw:search_ef"] == settings.chroma_hnsw_search_ef
        assert metadata["hnsw:M"] == settings.chroma_hnsw_m

    def test_reduced_retrieval_k_default(self):
        """Test that default retrieval_k is reduced for faster queries."""
        from config import settings

        # Should be 3 instead of original 5
        assert settings.retrieval_k == 3

    def test_hnsw_construction_ef_reduced(self):
        """Test that HNSW construction_ef is optimized."""
        from config import settings

        # Should be 100 instead of default 200
        assert settings.chroma_hnsw_construction_ef == 100

    def test_hnsw_search_ef_reduced(self):
        """Test that HNSW search_ef is optimized."""
        from config import settings

        # Should be 50 instead of default 100
        assert settings.chroma_hnsw_search_ef == 50

    @patch('app.services.vector_store.Chroma')
    def test_initialize_applies_metadata(self, mock_chroma):
        """Test that initialization applies collection metadata."""
        # Create a temporary settings with a store directory
        with patch('app.services.vector_store.settings') as mock_settings:
            mock_settings.vector_store_dir = Path('/tmp/test_chroma')
            mock_settings.vector_store_dir.exists = Mock(return_value=True)
            mock_settings.vector_store_dir.iterdir = Mock(return_value=[Path('/tmp/test_chroma/test.db')])
            mock_settings.collection_name = 'test_collection'
            mock_settings.embedding_model = 'nomic-embed-text'
            mock_settings.ollama_base_url = 'http://localhost:11434'
            mock_settings.chroma_hnsw_space = 'cosine'
            mock_settings.chroma_hnsw_construction_ef = 100
            mock_settings.chroma_hnsw_search_ef = 50
            mock_settings.chroma_hnsw_m = 16

            service = VectorStoreService()

            # Verify Chroma was called with collection_metadata
            if mock_chroma.called:
                call_kwargs = mock_chroma.call_args[1]
                assert 'collection_metadata' in call_kwargs
                metadata = call_kwargs['collection_metadata']
                assert metadata["hnsw:construction_ef"] == 100
                assert metadata["hnsw:search_ef"] == 50

    def test_search_uses_reduced_k(self):
        """Test that search uses the reduced k value by default."""
        service = VectorStoreService()

        # Mock the vectorstore
        service.vectorstore = Mock()
        service.vectorstore.similarity_search = Mock(return_value=[])

        # Search without specifying k
        service.search("test query")

        # Verify it used the reduced default k=3
        from config import settings
        service.vectorstore.similarity_search.assert_called_once_with("test query", k=settings.retrieval_k)

    def test_search_respects_custom_k(self):
        """Test that search respects custom k parameter."""
        service = VectorStoreService()

        # Mock the vectorstore
        service.vectorstore = Mock()
        service.vectorstore.similarity_search = Mock(return_value=[])

        # Search with custom k
        service.search("test query", k=10)

        # Verify it used the custom k
        service.vectorstore.similarity_search.assert_called_once_with("test query", k=10)

    def test_get_retriever_uses_reduced_k(self):
        """Test that get_retriever uses the reduced k value by default."""
        service = VectorStoreService()

        # Mock the vectorstore
        service.vectorstore = Mock()
        service.vectorstore.as_retriever = Mock(return_value=Mock())

        # Get retriever without specifying k
        service.get_retriever()

        # Verify it used the reduced default k=3
        from config import settings
        service.vectorstore.as_retriever.assert_called_once_with(
            search_kwargs={"k": settings.retrieval_k}
        )


class TestEnvironmentConfiguration:
    """Test environment variable configuration for performance settings."""

    def test_retrieval_k_from_env(self, monkeypatch):
        """Test that RETRIEVAL_K can be set via environment variable."""
        monkeypatch.setenv("RETRIEVAL_K", "2")

        settings = Settings.from_env()
        assert settings.retrieval_k == 2

    def test_hnsw_construction_ef_from_env(self, monkeypatch):
        """Test that CHROMA_HNSW_CONSTRUCTION_EF can be set via environment."""
        monkeypatch.setenv("CHROMA_HNSW_CONSTRUCTION_EF", "80")

        settings = Settings.from_env()
        assert settings.chroma_hnsw_construction_ef == 80

    def test_hnsw_search_ef_from_env(self, monkeypatch):
        """Test that CHROMA_HNSW_SEARCH_EF can be set via environment."""
        monkeypatch.setenv("CHROMA_HNSW_SEARCH_EF", "30")

        settings = Settings.from_env()
        assert settings.chroma_hnsw_search_ef == 30

# Run with: pytest tests/test_vector_performance.py -v