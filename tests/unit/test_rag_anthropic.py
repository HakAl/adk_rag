"""
Unit tests for RAG Anthropic service.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.rag_anthropic import RAGAnthropicService
from app.services.vector_store import VectorStoreService


@pytest.fixture
def mock_vector_store():
    """Create mock vector store."""
    vector_store = Mock(spec=VectorStoreService)
    return vector_store


@pytest.fixture
def mock_anthropic_client():
    """Create mock Anthropic client."""
    with patch('app.services.rag_anthropic.Anthropic') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def rag_anthropic_service(mock_vector_store, mock_anthropic_client):
    """Create RAG Anthropic service instance."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        service = RAGAnthropicService(mock_vector_store)
        return service


def test_initialization(mock_vector_store, mock_anthropic_client):
    """Test service initialization."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        service = RAGAnthropicService(mock_vector_store)
        assert service.vector_store == mock_vector_store
        assert service.model == "claude-sonnet-4-20250514"


def test_initialization_custom_model(mock_vector_store, mock_anthropic_client):
    """Test service initialization with custom model."""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test-key",
        "ANTHROPIC_MODEL": "claude-opus-4-20250514"
    }):
        service = RAGAnthropicService(mock_vector_store)
        assert service.model == "claude-opus-4-20250514"


def test_query_no_documents(rag_anthropic_service, mock_vector_store):
    """Test query when no documents in knowledge base."""
    mock_retriever = Mock()
    mock_retriever.invoke.side_effect = ValueError("No documents")
    mock_vector_store.get_retriever.return_value = mock_retriever

    answer, sources = rag_anthropic_service.query("test question")

    assert "No documents in knowledge base" in answer
    assert sources is None


def test_query_no_results(rag_anthropic_service, mock_vector_store):
    """Test query when retriever returns no results."""
    mock_retriever = Mock()
    mock_retriever.invoke.return_value = []
    mock_vector_store.get_retriever.return_value = mock_retriever

    answer, sources = rag_anthropic_service.query("test question")

    assert "No relevant information found" in answer
    assert sources is None


def test_query_success(rag_anthropic_service, mock_vector_store):
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

    # Mock Anthropic response
    mock_message = Mock()
    mock_message.content = [Mock(text="This is the answer")]
    rag_anthropic_service.client.messages.create.return_value = mock_message

    answer, sources = rag_anthropic_service.query("test question")

    assert "This is the answer" in answer
    assert sources == ["doc1.pdf", "doc2.pdf"]
    assert "📚 Sources:" in answer


def test_query_without_sources(rag_anthropic_service, mock_vector_store):
    """Test query without source citations."""
    mock_doc = Mock()
    mock_doc.page_content = "Test content"
    mock_doc.metadata = {"source": "/path/to/doc.pdf"}

    mock_retriever = Mock()
    mock_retriever.invoke.return_value = [mock_doc]
    mock_vector_store.get_retriever.return_value = mock_retriever

    mock_message = Mock()
    mock_message.content = [Mock(text="Answer")]
    rag_anthropic_service.client.messages.create.return_value = mock_message

    answer, sources = rag_anthropic_service.query("test", include_sources=False)

    assert answer == "Answer"
    assert sources is None
    assert "📚 Sources:" not in answer


def test_query_anthropic_api_error(rag_anthropic_service, mock_vector_store):
    """Test query when Anthropic API fails."""
    mock_doc = Mock()
    mock_doc.page_content = "Test content"
    mock_doc.metadata = {"source": "/path/to/doc.pdf"}

    mock_retriever = Mock()
    mock_retriever.invoke.return_value = [mock_doc]
    mock_vector_store.get_retriever.return_value = mock_retriever

    # Simulate API error
    rag_anthropic_service.client.messages.create.side_effect = Exception("API Error")

    answer, sources = rag_anthropic_service.query("test question")

    assert "Error generating answer" in answer
    assert sources == ["doc.pdf"]


def test_build_prompt(rag_anthropic_service):
    """Test prompt building."""
    contexts = ["Context 1", "Context 2"]
    prompt = rag_anthropic_service._build_prompt("What is X?", contexts)

    assert "Context 1" in prompt
    assert "Context 2" in prompt
    assert "What is X?" in prompt
    assert "[Context 1]" in prompt
    assert "[Context 2]" in prompt


def test_generate(rag_anthropic_service):
    """Test answer generation."""
    mock_message = Mock()
    mock_message.content = [Mock(text="Generated answer  ")]
    rag_anthropic_service.client.messages.create.return_value = mock_message

    answer = rag_anthropic_service._generate("test prompt")

    assert answer == "Generated answer"
    rag_anthropic_service.client.messages.create.assert_called_once()

    call_args = rag_anthropic_service.client.messages.create.call_args
    assert call_args[1]["model"] == "claude-sonnet-4-20250514"
    assert call_args[1]["max_tokens"] == 1024
    assert call_args[1]["messages"][0]["role"] == "user"
    assert call_args[1]["messages"][0]["content"] == "test prompt"