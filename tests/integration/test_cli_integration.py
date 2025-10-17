"""
Integration tests for CLI with API.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.cli.chat import CLI
from app.api.client import APIClient


@pytest.fixture
async def mock_api_client():
    """Create a mock API client."""
    client = AsyncMock(spec=APIClient)
    client.base_url = "http://test:8000"
    return client


@pytest.mark.asyncio
async def test_cli_initialization(mock_api_client):
    """Test CLI initialization with API client."""
    cli = CLI(mock_api_client)

    assert cli.api_client == mock_api_client
    assert cli.user_id == "cli_user"
    assert cli.session_id is None


@pytest.mark.asyncio
async def test_cli_connection_failure():
    """Test CLI handles API connection failure gracefully."""
    mock_client = AsyncMock(spec=APIClient)
    mock_client.health_check.side_effect = httpx.ConnectError("Connection failed")

    cli = CLI(mock_client)

    with patch('builtins.print') as mock_print:
        await cli.run()

        # Check that error message was printed
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Failed to connect" in str(call) for call in calls)


@pytest.mark.asyncio
async def test_cli_successful_connection_and_chat(mock_api_client):
    """Test CLI successfully connects and sends chat message."""
    # Mock API responses
    mock_api_client.health_check.return_value = {
        "status": "healthy",
        "version": "1.0.0"
    }
    mock_api_client.get_stats.return_value = {
        "app_name": "VIBE Agent",
        "version": "1.0.0",
        "environment": "test",
        "vector_store": {"status": "ready", "count": 100, "collection": "test"},
        "models": {"embedding": "nomic", "chat": "llama3.1"}
    }
    mock_api_client.create_session.return_value = "session-123"
    mock_api_client.chat.return_value = "Hello! How can I help?"

    cli = CLI(mock_api_client)

    # Mock prompt_toolkit input to simulate user typing "hello" then "exit"
    mock_prompt_session = AsyncMock()
    mock_prompt_session.prompt_async.side_effect = ["hello", "exit"]
    cli.prompt_session = mock_prompt_session

    with patch('builtins.print'):
        await cli.run()

    # Verify API calls were made
    mock_api_client.health_check.assert_called_once()
    mock_api_client.get_stats.assert_called_once()
    mock_api_client.create_session.assert_called_once_with("cli_user")
    mock_api_client.chat.assert_called_once_with(
        message="hello",
        user_id="cli_user",
        session_id="session-123"
    )


@pytest.mark.asyncio
async def test_cli_stats_command(mock_api_client):
    """Test stats command in CLI."""
    mock_stats = {
        "app_name": "VIBE Agent",
        "version": "1.0.0",
        "environment": "test",
        "vector_store": {"status": "ready", "count": 100, "collection": "test"},
        "models": {"embedding": "nomic", "chat": "llama3.1"}
    }

    mock_api_client.health_check.return_value = {"status": "healthy", "version": "1.0.0"}
    mock_api_client.get_stats.return_value = mock_stats
    mock_api_client.create_session.return_value = "session-123"

    cli = CLI(mock_api_client)

    # Simulate "stats" then "exit"
    mock_prompt_session = AsyncMock()
    mock_prompt_session.prompt_async.side_effect = ["stats", "exit"]
    cli.prompt_session = mock_prompt_session

    with patch('builtins.print') as mock_print:
        await cli.run()

    # Verify stats were called twice (once for banner, once for command)
    assert mock_api_client.get_stats.call_count == 2

    # Verify stats output was printed
    calls = [str(call) for call in mock_print.call_args_list]
    assert any("Application Statistics" in str(call) for call in calls)


@pytest.mark.asyncio
async def test_cli_new_session_command(mock_api_client):
    """Test creating new session in CLI."""
    mock_api_client.health_check.return_value = {"status": "healthy", "version": "1.0.0"}
    mock_api_client.get_stats.return_value = {
        "app_name": "VIBE Agent",
        "version": "1.0.0",
        "environment": "test",
        "vector_store": {"status": "ready", "count": 100, "collection": "test"},
        "models": {"embedding": "nomic", "chat": "llama3.1"}
    }
    mock_api_client.create_session.side_effect = ["session-1", "session-2"]

    cli = CLI(mock_api_client)

    # Simulate "new" then "exit"
    mock_prompt_session = AsyncMock()
    mock_prompt_session.prompt_async.side_effect = ["new", "exit"]
    cli.prompt_session = mock_prompt_session

    with patch('builtins.print'):
        await cli.run()

    # Verify two sessions were created
    assert mock_api_client.create_session.call_count == 2


@pytest.mark.asyncio
async def test_cli_handles_chat_error(mock_api_client):
    """Test CLI handles chat API errors gracefully."""
    mock_api_client.health_check.return_value = {"status": "healthy", "version": "1.0.0"}
    mock_api_client.get_stats.return_value = {
        "app_name": "VIBE Agent",
        "version": "1.0.0",
        "environment": "test",
        "vector_store": {"status": "ready", "count": 100, "collection": "test"},
        "models": {"embedding": "nomic", "chat": "llama3.1"}
    }
    mock_api_client.create_session.return_value = "session-123"
    mock_api_client.chat.side_effect = httpx.HTTPStatusError(
        "Internal Server Error", request=AsyncMock(), response=AsyncMock()
    )

    cli = CLI(mock_api_client)

    # Simulate a message that will fail, then exit
    mock_prompt_session = AsyncMock()
    mock_prompt_session.prompt_async.side_effect = ["test message", "exit"]
    cli.prompt_session = mock_prompt_session

    with patch('builtins.print') as mock_print:
        await cli.run()

    # Verify error was printed
    calls = [str(call) for call in mock_print.call_args_list]
    assert any("API Error" in str(call) for call in calls)