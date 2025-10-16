"""
Unit tests for RAG Google service.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.rag_google import RAGGoogleService
from app.services.vector_store import VectorStoreService


@pytest.fixture
def mock_vector_store():
    """Create mock vector store."""
    vector_store = Mock(spec=VectorStoreService)
    return vector_store


@pytest.fixture
def mock_genai():
    """Create mock Google GenAI."""
    with patch('app.services.rag_google.genai') as mock:
        yield mock


@pytest.fixture
def rag_google_service(mock_vector_store, mock_genai):
    """Create RAG Google service instance."""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        service = RAGGoogleService(mock_vector_store)
        return service


def test_initialization(mock_vector_store, mock_genai):
    """Test service initialization."""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        service = RAGGoogleService(mock_vector_store)
        assert service.vector_store == mock_vector_store
        assert service.model_name == "gemini-2.0-flash-exp"
        mock_genai.configure.assert_called_once_with(api_key="test-key")


def test_initialization_custom_model(mock_vector_store, mock_genai):
    """Test service initialization with custom model."""
    with patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test-key",
        "GOOGLE_MODEL": "gemini-1.5-pro"
    }):
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        service = RAGGoogleService(mock_vector_store)
        assert service.model_name == "gemini-1.5-pro"


def test_query_no_documents(rag_google_service, mock_vector_store):
    """Test query when no documents in knowledge base."""
    mock_retriever = Mock()
    mock_retriever.invoke.side_effect = ValueError("No documents")
    mock_vector_store.get_retriever.return_value = mock_retriever

    answer, sources = rag_google_service.query("test question")

    assert "No documents in knowledge base" in answer
    assert sources is None


def test_query_no_results(rag_google_service, mock_vector_store):
    """Test query when retriever returns no results."""
    mock_retriever = Mock()
    mock_retriever.invoke.return_value = []
    mock_vector_store.get_retriever.return_value = mock_retriever

    answer, sources = rag_google_service.query("test question")

    assert "No relevant information found" in answer
    assert sources is None


def test_query_success(rag_google_service, mock_vector_store):
    """Test successful query."""
    # Mock document results
    mock_doc1 = Mock()
    mock_doc1.page_content = "Test content 1"
    mock_doc1.metadata = {"source": "/path/to/doc1.pdf"}

    mock_doc2 = Mock()
    mock_doc2.page_content = "Test content 2"
    mock_doc2.metadata = {"source": "/path/to/doc2.pdf"}

    mock_retriever = Mock()
    mock_retriever.invoke.return_value = [mock_doc1, mock_doc2]
    mock_vector_store.get_retriever.return_value = mock_retriever

    # Mock Google response
    mock_response = Mock()
    mock_response.text = "This is the answer"
    rag_google_service.model.generate_content.return_value = mock_response

    answer, sources = rag_google_service.query("test question")

    assert "This is the answer" in answer
    assert sources == ["doc1.pdf", "doc2.pdf"]
    assert "📚 Sources:" in answer


def test_query_without_sources(rag_google_service, mock_vector_store):
    """Test query without source citations."""
    mock_doc = Mock()
    mock_doc.page_content = "Test content"
    mock_doc.metadata = {"source": "/path/to/doc.pdf"}

    mock_retriever = Mock()
    mock_retriever.invoke.return_value = [mock_doc]
    mock_vector_store.get_retriever.return_value = mock_retriever

    mock_response = Mock()
    mock_response.text = "Answer"
    rag_google_service.model.generate_content.return_value = mock_response

    answer, sources = rag_google_service.query("test", include_sources=False)

    assert answer == "Answer"
    assert sources is None
    assert "📚 Sources:" not in answer


def test_query_google_api_error(rag_google_service, mock_vector_store):
    """Test query when Google API fails."""
    mock_doc = Mock()
    mock_doc.page_content = "Test content"
    mock_doc.metadata = {"source": "/path/to/doc.pdf"}

    mock_retriever = Mock()
    mock_retriever.invoke.return_value = [mock_doc]
    mock_vector_store.get_retriever.return_value = mock_retriever

    # Simulate API error
    rag_google_service.model.generate_content.side_effect = Exception("API Error")

    answer, sources = rag_google_service.query("test question")

    assert "Error generating answer" in answer
    assert sources == ["doc.pdf"]


def test_build_prompt(rag_google_service):
    """Test prompt building."""
    contexts = ["Context 1", "Context 2"]
    prompt = rag_google_service._build_prompt("What is X?", contexts)

    assert "Context 1" in prompt
    assert "Context 2" in prompt
    assert "What is X?" in prompt
    assert "[Context 1]" in prompt
    assert "[Context 2]" in prompt


def test_generate(rag_google_service):
    """Test answer generation."""
    mock_response = Mock()
    mock_response.text = "Generated answer  "
    rag_google_service.model.generate_content.return_value = mock_response

    answer = rag_google_service._generate("test prompt")

    assert answer == "Generated answer"
    rag_google_service.model.generate_content.assert_called_once_with("test prompt")