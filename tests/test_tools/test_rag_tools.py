"""
Tests for RAG tools.
"""
import pytest
from unittest.mock import Mock, MagicMock

from app.tools.rag_tools import (
    create_rag_query_tool,
    create_rag_anthropic_tool,
    create_rag_google_tool,
    create_rag_tools
)


class TestCreateRAGQueryTool:
    """Tests for create_rag_query_tool."""

    def test_creates_callable(self):
        mock_service = Mock()
        tool = create_rag_query_tool(mock_service)
        assert callable(tool)

    def test_tool_calls_service_query(self):
        mock_service = Mock()
        mock_service.query.return_value = ("Answer text", ["source1.pdf"])

        tool = create_rag_query_tool(mock_service)
        result = tool("What is RAG?")

        mock_service.query.assert_called_once_with("What is RAG?")
        assert result == "Answer text"

    def test_tool_handles_service_error(self):
        mock_service = Mock()
        mock_service.query.return_value = ("❌ Error: something failed", None)

        tool = create_rag_query_tool(mock_service)
        result = tool("test query")

        assert "❌" in result

    def test_tool_docstring_preserved(self):
        mock_service = Mock()
        tool = create_rag_query_tool(mock_service)

        assert tool.__doc__ is not None
        assert "knowledge base" in tool.__doc__.lower()


class TestCreateRAGAnthropicTool:
    """Tests for create_rag_anthropic_tool."""

    def test_creates_callable(self):
        mock_service = Mock()
        tool = create_rag_anthropic_tool(mock_service)
        assert callable(tool)

    def test_tool_calls_service_query(self):
        mock_service = Mock()
        mock_service.query.return_value = ("Anthropic answer", ["doc.pdf"])

        tool = create_rag_anthropic_tool(mock_service)
        result = tool("Complex question?")

        mock_service.query.assert_called_once_with("Complex question?")
        assert result == "Anthropic answer"

    def test_tool_docstring_mentions_anthropic(self):
        mock_service = Mock()
        tool = create_rag_anthropic_tool(mock_service)

        assert tool.__doc__ is not None
        assert "anthropic" in tool.__doc__.lower() or "claude" in tool.__doc__.lower()


class TestCreateRAGGoogleTool:
    """Tests for create_rag_google_tool."""

    def test_creates_callable(self):
        mock_service = Mock()
        tool = create_rag_google_tool(mock_service)
        assert callable(tool)

    def test_tool_calls_service_query(self):
        mock_service = Mock()
        mock_service.query.return_value = ("Google answer", ["file.pdf"])

        tool = create_rag_google_tool(mock_service)
        result = tool("Factual question?")

        mock_service.query.assert_called_once_with("Factual question?")
        assert result == "Google answer"

    def test_tool_docstring_mentions_google(self):
        mock_service = Mock()
        tool = create_rag_google_tool(mock_service)

        assert tool.__doc__ is not None
        assert "google" in tool.__doc__.lower() or "gemini" in tool.__doc__.lower()


class TestCreateRAGTools:
    """Tests for create_rag_tools factory function."""

    def test_creates_list_with_only_local_rag(self):
        mock_rag_service = Mock()
        tools = create_rag_tools(mock_rag_service)

        assert isinstance(tools, list)
        assert len(tools) == 1
        assert callable(tools[0])

    def test_creates_list_with_anthropic(self):
        mock_rag_service = Mock()
        mock_anthropic_service = Mock()

        tools = create_rag_tools(
            rag_service=mock_rag_service,
            rag_anthropic_service=mock_anthropic_service
        )

        assert len(tools) == 2

    def test_creates_list_with_google(self):
        mock_rag_service = Mock()
        mock_google_service = Mock()

        tools = create_rag_tools(
            rag_service=mock_rag_service,
            rag_google_service=mock_google_service
        )

        assert len(tools) == 2

    def test_creates_list_with_all_services(self):
        mock_rag_service = Mock()
        mock_anthropic_service = Mock()
        mock_google_service = Mock()

        tools = create_rag_tools(
            rag_service=mock_rag_service,
            rag_anthropic_service=mock_anthropic_service,
            rag_google_service=mock_google_service
        )

        assert len(tools) == 3
        for tool in tools:
            assert callable(tool)

    def test_tools_are_independent(self):
        """Test that each tool maintains its own closure."""
        mock_rag_service = Mock()
        mock_rag_service.query.return_value = ("Local answer", None)

        mock_anthropic_service = Mock()
        mock_anthropic_service.query.return_value = ("Anthropic answer", None)

        tools = create_rag_tools(
            rag_service=mock_rag_service,
            rag_anthropic_service=mock_anthropic_service
        )

        # Call first tool
        result1 = tools[0]("test")
        assert result1 == "Local answer"
        mock_rag_service.query.assert_called_once()

        # Call second tool
        result2 = tools[1]("test")
        assert result2 == "Anthropic answer"
        mock_anthropic_service.query.assert_called_once()


class TestToolClosures:
    """Tests to verify closure behavior works correctly."""

    def test_closure_captures_correct_service(self):
        """Verify each tool captures the correct service instance."""
        service1 = Mock()
        service1.query.return_value = ("Service 1", None)

        service2 = Mock()
        service2.query.return_value = ("Service 2", None)

        tool1 = create_rag_query_tool(service1)
        tool2 = create_rag_query_tool(service2)

        assert tool1("test") == "Service 1"
        assert tool2("test") == "Service 2"

    def test_closure_persists_across_calls(self):
        """Verify closure state persists across multiple calls."""
        mock_service = Mock()
        mock_service.query.side_effect = [
            ("Answer 1", None),
            ("Answer 2", None),
            ("Answer 3", None)
        ]

        tool = create_rag_query_tool(mock_service)

        assert tool("query1") == "Answer 1"
        assert tool("query2") == "Answer 2"
        assert tool("query3") == "Answer 3"
        assert mock_service.query.call_count == 3