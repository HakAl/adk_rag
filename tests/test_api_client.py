"""
Tests for API client.
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.api.client import APIClient


@pytest.fixture
async def api_client():
    """Create API client for testing."""
    client = APIClient(base_url="http://test:8000", timeout=5)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_health_check_success(api_client):
    """Test successful health check."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {"status": "healthy", "version": "1.0.0"}
    mock_response.raise_for_status = AsyncMock()

    with patch.object(api_client.client, 'get', return_value=mock_response):
        result = await api_client.health_check()

        assert result["status"] == "healthy"
        assert result["version"] == "1.0.0"
        api_client.client.get.assert_called_once_with("/health")


@pytest.mark.asyncio
async def test_health_check_failure(api_client):
    """Test health check with API error."""
    mock_response = AsyncMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=AsyncMock(), response=AsyncMock()
    )

    with patch.object(api_client.client, 'get', return_value=mock_response):
        with pytest.raises(httpx.HTTPStatusError):
            await api_client.health_check()


@pytest.mark.asyncio
async def test_get_stats(api_client):
    """Test getting application statistics."""
    mock_stats = {
        "app_name": "VIBE Agent",
        "version": "1.0.0",
        "environment": "test",
        "vector_store": {"status": "ready", "count": 100},
        "models": {"embedding": "nomic", "chat": "llama3.1"}
    }

    mock_response = AsyncMock()
    mock_response.json.return_value = mock_stats
    mock_response.raise_for_status = AsyncMock()

    with patch.object(api_client.client, 'get', return_value=mock_response):
        result = await api_client.get_stats()

        assert result["app_name"] == "VIBE Agent"
        assert result["vector_store"]["count"] == 100
        api_client.client.get.assert_called_once_with("/stats")


@pytest.mark.asyncio
async def test_create_session(api_client):
    """Test creating a new session."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "session_id": "test-session-123",
        "user_id": "test_user"
    }
    mock_response.raise_for_status = AsyncMock()

    with patch.object(api_client.client, 'post', return_value=mock_response):
        session_id = await api_client.create_session("test_user")

        assert session_id == "test-session-123"
        api_client.client.post.assert_called_once_with(
            "/sessions",
            json={"user_id": "test_user"}
        )


@pytest.mark.asyncio
async def test_chat(api_client):
    """Test sending a chat message."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "response": "Hello! How can I help?",
        "session_id": "test-session-123"
    }
    mock_response.raise_for_status = AsyncMock()

    with patch.object(api_client.client, 'post', return_value=mock_response):
        response = await api_client.chat(
            message="Hi there",
            user_id="test_user",
            session_id="test-session-123"
        )

        assert response == "Hello! How can I help?"
        api_client.client.post.assert_called_once_with(
            "/chat",
            json={
                "message": "Hi there",
                "user_id": "test_user",
                "session_id": "test-session-123"
            }
        )


@pytest.mark.asyncio
async def test_chat_with_api_error(api_client):
    """Test chat with API error."""
    mock_response = AsyncMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Internal Server Error", request=AsyncMock(), response=AsyncMock()
    )

    with patch.object(api_client.client, 'post', return_value=mock_response):
        with pytest.raises(httpx.HTTPStatusError):
            await api_client.chat(
                message="Hi",
                user_id="test_user",
                session_id="test-session"
            )


@pytest.mark.asyncio
async def test_custom_base_url_and_timeout():
    """Test creating client with custom settings."""
    client = APIClient(base_url="http://custom:9000", timeout=60)

    assert client.base_url == "http://custom:9000"
    assert client.timeout == 60

    await client.close()


@pytest.mark.asyncio
async def test_default_settings():
    """Test creating client with default settings."""
    with patch('app.api.client.settings') as mock_settings:
        mock_settings.api_base_url = "http://localhost:8000"
        mock_settings.api_timeout = 30

        client = APIClient()

        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30

        await client.close()