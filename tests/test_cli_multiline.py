"""
Tests for multiline CLI input handling with prompt_toolkit.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.cli.chat import CLI
from app.core.application import RAGAgentApp


class TestPromptToolkitMultiline:
    """Tests for prompt_toolkit multiline input."""

    @pytest.mark.asyncio
    @patch('app.cli.chat.PromptSession')
    async def test_single_line_input(self, mock_prompt_session_class):
        """Test single line input."""
        mock_session = Mock()
        mock_session.prompt_async = AsyncMock(return_value="Hello, single line")
        mock_prompt_session_class.return_value = mock_session

        mock_app = Mock(spec=RAGAgentApp)
        mock_app.create_session = AsyncMock(return_value="session-123")
        mock_app.chat = AsyncMock(return_value="Response")
        mock_app.get_stats = Mock(return_value={
            'app_name': 'Test',
            'version': '1.0',
            'environment': 'test',
            'vector_store': {'status': 'ready', 'count': 100, 'collection': 'test'},
            'models': {'embedding': 'test', 'chat': 'test'}
        })

        cli = CLI(mock_app)

        # Simulate one query then exit
        mock_session.prompt_async.side_effect = [
            "Hello, single line",
            "exit"
        ]

        await cli.run()

        # Verify chat was called with single line
        assert mock_app.chat.call_count == 1
        call_args = mock_app.chat.call_args[1]
        assert call_args['message'] == "Hello, single line"

    @pytest.mark.asyncio
    @patch('app.cli.chat.PromptSession')
    async def test_multiline_paste(self, mock_prompt_session_class):
        """Test multiline paste input."""
        mock_session = Mock()
        mock_session.prompt_async = AsyncMock()
        mock_prompt_session_class.return_value = mock_session

        mock_app = Mock(spec=RAGAgentApp)
        mock_app.create_session = AsyncMock(return_value="session-123")
        mock_app.chat = AsyncMock(return_value="Response")
        mock_app.get_stats = Mock(return_value={
            'app_name': 'Test',
            'version': '1.0',
            'environment': 'test',
            'vector_store': {'status': 'ready', 'count': 100, 'collection': 'test'},
            'models': {'embedding': 'test', 'chat': 'test'}
        })

        cli = CLI(mock_app)

        # Simulate pasted multiline input
        multiline_code = """def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count"""

        mock_session.prompt_async.side_effect = [
            multiline_code,
            "exit"
        ]

        await cli.run()

        # Verify chat was called with full multiline content
        assert mock_app.chat.call_count == 1
        call_args = mock_app.chat.call_args[1]
        assert "def calculate_average(numbers):" in call_args['message']
        assert "total = sum(numbers)" in call_args['message']
        assert "count = len(numbers)" in call_args['message']
        assert "return total / count" in call_args['message']

    @pytest.mark.asyncio
    @patch('app.cli.chat.PromptSession')
    async def test_multiline_with_empty_lines(self, mock_prompt_session_class):
        """Test multiline input preserves empty lines."""
        mock_session = Mock()
        mock_session.prompt_async = AsyncMock()
        mock_prompt_session_class.return_value = mock_session

        mock_app = Mock(spec=RAGAgentApp)
        mock_app.create_session = AsyncMock(return_value="session-123")
        mock_app.chat = AsyncMock(return_value="Response")
        mock_app.get_stats = Mock(return_value={
            'app_name': 'Test',
            'version': '1.0',
            'environment': 'test',
            'vector_store': {'status': 'ready', 'count': 100, 'collection': 'test'},
            'models': {'embedding': 'test', 'chat': 'test'}
        })

        cli = CLI(mock_app)

        # Multiline with empty line
        multiline_text = "First paragraph\n\nSecond paragraph"

        mock_session.prompt_async.side_effect = [
            multiline_text,
            "exit"
        ]

        await cli.run()

        # Verify empty lines preserved
        call_args = mock_app.chat.call_args[1]
        assert "\n\n" in call_args['message']

    @pytest.mark.asyncio
    @patch('app.cli.chat.PromptSession')
    async def test_special_commands_still_work(self, mock_prompt_session_class):
        """Test special commands work with prompt_toolkit."""
        mock_session = Mock()
        mock_session.prompt_async = AsyncMock()
        mock_prompt_session_class.return_value = mock_session

        mock_app = Mock(spec=RAGAgentApp)
        mock_app.create_session = AsyncMock(return_value="session-123")
        mock_app.chat = AsyncMock(return_value="Response")
        mock_app.get_stats = Mock(return_value={
            'app_name': 'Test',
            'version': '1.0',
            'environment': 'test',
            'vector_store': {'status': 'ready', 'count': 100, 'collection': 'test'},
            'models': {'embedding': 'test', 'chat': 'test'}
        })

        cli = CLI(mock_app)

        # Test stats command then exit
        mock_session.prompt_async.side_effect = [
            "stats",
            "exit"
        ]

        with patch('builtins.print'):
            await cli.run()

        # Stats command should not trigger chat
        assert mock_app.chat.call_count == 0


class TestCLIIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    @patch('app.cli.chat.PromptSession')
    async def test_full_conversation_flow(self, mock_prompt_session_class):
        """Test full conversation with multiple inputs."""
        mock_session = Mock()
        mock_session.prompt_async = AsyncMock()
        mock_prompt_session_class.return_value = mock_session

        mock_app = Mock(spec=RAGAgentApp)
        mock_app.create_session = AsyncMock(return_value="session-123")
        mock_app.chat = AsyncMock(return_value="Response")
        mock_app.get_stats = Mock(return_value={
            'app_name': 'Test',
            'version': '1.0',
            'environment': 'test',
            'vector_store': {'status': 'ready', 'count': 100, 'collection': 'test'},
            'models': {'embedding': 'test', 'chat': 'test'}
        })

        cli = CLI(mock_app)

        # Multiple queries
        mock_session.prompt_async.side_effect = [
            "First question",
            "def foo():\n    return 'bar'",
            "Third question",
            "exit"
        ]

        with patch('builtins.print'):
            await cli.run()

        # Verify all queries processed
        assert mock_app.chat.call_count == 3