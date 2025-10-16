"""
Integration tests for RAGAgentApp with multi-provider support.
"""
import os
import pytest
from unittest.mock import patch, Mock
from app.core.application import RAGAgentApp


@pytest.fixture
def mock_services():
    """Mock all service dependencies."""
    with patch('app.core.application.VectorStoreService') as mock_vs, \
         patch('app.core.application.RAGService') as mock_rag, \
         patch('app.core.application.RAGAnthropicService') as mock_anthropic, \
         patch('app.core.application.RAGGoogleService') as mock_google, \
         patch('app.core.application.ADKAgentService') as mock_adk:

        yield {
            'vector_store': mock_vs,
            'rag': mock_rag,
            'anthropic': mock_anthropic,
            'google': mock_google,
            'adk': mock_adk
        }


def test_app_initialization_no_providers(mock_services):
    """Test app initialization without external providers."""
    with patch.dict(os.environ, {}, clear=True):
        app = RAGAgentApp()

        assert app.rag_service is not None
        assert app.rag_anthropic_service is None
        assert app.rag_google_service is None


def test_app_initialization_with_anthropic(mock_services):
    """Test app initialization with Anthropic provider."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        app = RAGAgentApp()

        assert app.rag_service is not None
        assert app.rag_anthropic_service is not None
        assert app.rag_google_service is None


def test_app_initialization_with_google(mock_services):
    """Test app initialization with Google provider."""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
        app = RAGAgentApp()

        assert app.rag_service is not None
        assert app.rag_anthropic_service is None
        assert app.rag_google_service is not None


def test_app_initialization_with_all_providers(mock_services):
    """Test app initialization with all providers."""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GOOGLE_API_KEY": "test-google-key"
    }):
        app = RAGAgentApp()

        assert app.rag_service is not None
        assert app.rag_anthropic_service is not None
        assert app.rag_google_service is not None


def test_app_initialization_anthropic_fails_gracefully(mock_services):
    """Test that app continues if Anthropic initialization fails."""
    mock_services['anthropic'].side_effect = Exception("API Error")

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        app = RAGAgentApp()

        assert app.rag_service is not None
        assert app.rag_anthropic_service is None


def test_app_initialization_google_fails_gracefully(mock_services):
    """Test that app continues if Google initialization fails."""
    mock_services['google'].side_effect = Exception("API Error")

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
        app = RAGAgentApp()

        assert app.rag_service is not None
        assert app.rag_google_service is None


def test_get_stats_no_providers(mock_services):
    """Test get_stats with no external providers."""
    mock_vector_store = mock_services['vector_store'].return_value
    mock_vector_store.get_stats.return_value = {
        "status": "ready",
        "count": 100
    }

    with patch.dict(os.environ, {}, clear=True):
        app = RAGAgentApp()
        stats = app.get_stats()

        assert stats['providers']['local'] is True
        assert stats['providers']['anthropic'] is False
        assert stats['providers']['google'] is False


def test_get_stats_with_all_providers(mock_services):
    """Test get_stats with all providers."""
    mock_vector_store = mock_services['vector_store'].return_value
    mock_vector_store.get_stats.return_value = {
        "status": "ready",
        "count": 100
    }

    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test-key1",
        "GOOGLE_API_KEY": "test-key2"
    }):
        app = RAGAgentApp()
        stats = app.get_stats()

        assert stats['providers']['local'] is True
        assert stats['providers']['anthropic'] is True
        assert stats['providers']['google'] is True


def test_query_rag_local_provider(mock_services):
    """Test querying with local provider."""
    mock_rag = mock_services['rag'].return_value
    mock_rag.query.return_value = ("Answer", ["source.pdf"])

    with patch.dict(os.environ, {}, clear=True):
        app = RAGAgentApp()
        app.rag_service = mock_rag

        answer, sources = app.query_rag("test question", provider="local")

        assert answer == "Answer"
        assert sources == ["source.pdf"]
        mock_rag.query.assert_called_once()


def test_query_rag_anthropic_provider(mock_services):
    """Test querying with Anthropic provider."""
    mock_anthropic = mock_services['anthropic'].return_value
    mock_anthropic.query.return_value = ("Anthropic Answer", ["source.pdf"])

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        app = RAGAgentApp()
        app.rag_anthropic_service = mock_anthropic

        answer, sources = app.query_rag("test question", provider="anthropic")

        assert answer == "Anthropic Answer"
        mock_anthropic.query.assert_called_once()


def test_query_rag_google_provider(mock_services):
    """Test querying with Google provider."""
    mock_google = mock_services['google'].return_value
    mock_google.query.return_value = ("Google Answer", ["source.pdf"])

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
        app = RAGAgentApp()
        app.rag_google_service = mock_google

        answer, sources = app.query_rag("test question", provider="google")

        assert answer == "Google Answer"
        mock_google.query.assert_called_once()


def test_query_rag_fallback_to_local(mock_services):
    """Test that querying falls back to local if requested provider unavailable."""
    mock_rag = mock_services['rag'].return_value
    mock_rag.query.return_value = ("Local Answer", ["source.pdf"])

    with patch.dict(os.environ, {}, clear=True):
        app = RAGAgentApp()
        app.rag_service = mock_rag

        # Request Anthropic but it's not available
        answer, sources = app.query_rag("test question", provider="anthropic")

        # Should fall back to local
        assert answer == "Local Answer"
        mock_rag.query.assert_called_once()


def test_adk_agent_receives_all_services(mock_services):
    """Test that ADK agent is initialized with all available services."""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test-key1",
        "GOOGLE_API_KEY": "test-key2"
    }):
        app = RAGAgentApp()

        # Check ADKAgentService was called with all services
        call_args = mock_services['adk'].call_args
        assert call_args[0][0] is not None  # rag_service
        assert call_args[0][1] is not None  # rag_anthropic_service
        assert call_args[0][2] is not None  # rag_google_service