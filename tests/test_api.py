"""
Tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from app.api.main import app, get_app
from app.core.application import RAGAgentApp


@pytest.fixture
def mock_rag_app():
    """Mock RAG application."""
    app = Mock(spec=RAGAgentApp)
    app.get_stats = Mock(return_value={
        "app_name": "RAG Agent",
        "version": "1.0.0",
        "environment": "test",
        "vector_store": {
            "status": "ready",
            "count": 100,
            "collection": "test_collection"
        },
        "models": {
            "embedding": "test-embed",
            "chat": "test-chat"
        }
    })
    app.create_session = AsyncMock(return_value="test-session-123")
    app.chat = AsyncMock(return_value="Test response")
    return app


@pytest.fixture
def client(mock_rag_app):
    """Test client with mocked dependencies."""
    app.dependency_overrides[get_app] = lambda: mock_rag_app
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestStatsEndpoint:
    """Tests for statistics endpoint."""

    def test_get_stats_success(self, client, mock_rag_app):
        """Test getting application statistics."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "RAG Agent"
        assert data["version"] == "1.0.0"
        assert "vector_store" in data
        assert "models" in data

    def test_get_stats_error(self, client, mock_rag_app):
        """Test stats endpoint error handling."""
        mock_rag_app.get_stats.side_effect = Exception("Test error")
        response = client.get("/stats")
        assert response.status_code == 500


class TestSessionEndpoint:
    """Tests for session creation endpoint."""

    def test_create_session_default_user(self, client, mock_rag_app):
        """Test creating session with default user."""
        response = client.post("/sessions", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"
        assert data["user_id"] == "api_user"
        mock_rag_app.create_session.assert_called_once_with("api_user")

    def test_create_session_custom_user(self, client, mock_rag_app):
        """Test creating session with custom user."""
        response = client.post("/sessions", json={"user_id": "custom_user"})
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"
        assert data["user_id"] == "custom_user"
        mock_rag_app.create_session.assert_called_once_with("custom_user")

    def test_create_session_error(self, client, mock_rag_app):
        """Test session creation error handling."""
        mock_rag_app.create_session.side_effect = Exception("Session error")
        response = client.post("/sessions", json={})
        assert response.status_code == 500


class TestChatEndpoint:
    """Tests for chat endpoint."""

    def test_chat_success(self, client, mock_rag_app):
        """Test successful chat interaction."""
        request_data = {
            "message": "What is AI?",
            "user_id": "test_user",
            "session_id": "test-session-123"
        }
        response = client.post("/chat", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response"
        assert data["session_id"] == "test-session-123"
        mock_rag_app.chat.assert_called_once_with(
            message="What is AI?",
            user_id="test_user",
            session_id="test-session-123"
        )

    def test_chat_empty_message(self, client):
        """Test chat with empty message."""
        request_data = {
            "message": "",
            "user_id": "test_user",
            "session_id": "test-session-123"
        }
        response = client.post("/chat", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_chat_missing_fields(self, client):
        """Test chat with missing required fields."""
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 422

    def test_chat_error(self, client, mock_rag_app):
        """Test chat error handling."""
        mock_rag_app.chat.side_effect = Exception("Chat error")
        request_data = {
            "message": "Test",
            "user_id": "test_user",
            "session_id": "test-session-123"
        }
        response = client.post("/chat", json=request_data)
        assert response.status_code == 500


class TestValidation:
    """Tests for request validation."""

    def test_chat_request_validation(self, client):
        """Test chat request validation rules."""
        # Missing message
        response = client.post("/chat", json={
            "user_id": "test",
            "session_id": "test"
        })
        assert response.status_code == 422

        # Empty message
        response = client.post("/chat", json={
            "message": "",
            "user_id": "test",
            "session_id": "test"
        })
        assert response.status_code == 422

        # Missing user_id
        response = client.post("/chat", json={
            "message": "test",
            "session_id": "test"
        })
        assert response.status_code == 422

        # Missing session_id
        response = client.post("/chat", json={
            "message": "test",
            "user_id": "test"
        })
        assert response.status_code == 422


class TestDependencyInjection:
    """Tests for dependency injection."""

    def test_app_not_initialized(self):
        """Test endpoint when app is not initialized."""
        # Create client without overriding dependency
        client = TestClient(app)

        # Mock the global rag_app as None
        with patch('app.api.main.rag_app', None):
            response = client.get("/stats")
            assert response.status_code == 503
            assert "not initialized" in response.json()["detail"].lower()