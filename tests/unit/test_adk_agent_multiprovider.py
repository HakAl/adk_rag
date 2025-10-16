"""
Unit tests for ADK Agent service with multi-provider support.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.adk_agent import ADKAgentService
from app.services.rag import RAGService
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService


@pytest.fixture
def mock_rag_service():
    """Create mock RAG service."""
    service = Mock(spec=RAGService)
    service.query.return_value = ("Local answer", ["source.pdf"])
    return service


@pytest.fixture
def mock_rag_anthropic_service():
    """Create mock RAG Anthropic service."""
    service = Mock(spec=RAGAnthropicService)
    service.query.return_value = ("Anthropic answer", ["source.pdf"])
    return service


@pytest.fixture
def mock_rag_google_service():
    """Create mock RAG Google service."""
    service = Mock(spec=RAGGoogleService)
    service.query.return_value = ("Google answer", ["source.pdf"])
    return service


@pytest.fixture
def adk_agent_local_only(mock_rag_service):
    """Create ADK agent with only local provider."""
    with patch('app.services.adk_agent.LiteLlm'), \
            patch('app.services.adk_agent.LlmAgent'), \
            patch('app.services.adk_agent.Runner'):
        agent = ADKAgentService(mock_rag_service)
        return agent


@pytest.fixture
def adk_agent_all_providers(mock_rag_service, mock_rag_anthropic_service, mock_rag_google_service):
    """Create ADK agent with all providers."""
    with patch('app.services.adk_agent.LiteLlm'), \
            patch('app.services.adk_agent.LlmAgent'), \
            patch('app.services.adk_agent.Runner'):
        agent = ADKAgentService(
            mock_rag_service,
            mock_rag_anthropic_service,
            mock_rag_google_service
        )
        return agent


def test_initialization_local_only(adk_agent_local_only, mock_rag_service):
    """Test initialization with only local provider."""
    assert adk_agent_local_only.rag_service == mock_rag_service
    assert adk_agent_local_only.rag_anthropic_service is None
    assert adk_agent_local_only.rag_google_service is None


def test_initialization_all_providers(adk_agent_all_providers, mock_rag_service,
                                      mock_rag_anthropic_service, mock_rag_google_service):
    """Test initialization with all providers."""
    assert adk_agent_all_providers.rag_service == mock_rag_service
    assert adk_agent_all_providers.rag_anthropic_service == mock_rag_anthropic_service
    assert adk_agent_all_providers.rag_google_service == mock_rag_google_service


def test_create_agent_local_only(mock_rag_service):
    """Test agent creation with only local provider."""
    with patch('app.services.adk_agent.LiteLlm') as mock_llm, \
            patch('app.services.adk_agent.LlmAgent') as mock_agent_class, \
            patch('app.services.adk_agent.Runner'):
        agent_service = ADKAgentService(mock_rag_service)

        # Verify LlmAgent was called with correct number of tools
        call_kwargs = mock_agent_class.call_args[1]
        assert len(call_kwargs['tools']) == 1
        assert 'rag_query()' in call_kwargs['instruction']


def test_create_agent_all_providers(mock_rag_service, mock_rag_anthropic_service, mock_rag_google_service):
    """Test agent creation with all providers."""
    with patch('app.services.adk_agent.LiteLlm') as mock_llm, \
            patch('app.services.adk_agent.LlmAgent') as mock_agent_class, \
            patch('app.services.adk_agent.Runner'):
        agent_service = ADKAgentService(
            mock_rag_service,
            mock_rag_anthropic_service,
            mock_rag_google_service
        )

        # Verify LlmAgent was called with all tools
        call_kwargs = mock_agent_class.call_args[1]
        assert len(call_kwargs['tools']) == 3
        assert 'rag_query()' in call_kwargs['instruction']
        assert 'rag_query_anthropic()' in call_kwargs['instruction']
        assert 'rag_query_google()' in call_kwargs['instruction']


def test_rag_query_tool(adk_agent_local_only, mock_rag_service):
    """Test local RAG query tool."""
    result = adk_agent_local_only._rag_query_tool("test query")

    assert result == "Local answer"
    mock_rag_service.query.assert_called_once_with("test query")


def test_rag_query_anthropic_tool(adk_agent_all_providers, mock_rag_anthropic_service):
    """Test Anthropic RAG query tool."""
    result = adk_agent_all_providers._rag_query_anthropic_tool("test query")

    assert result == "Anthropic answer"
    mock_rag_anthropic_service.query.assert_called_once_with("test query")


def test_rag_query_google_tool(adk_agent_all_providers, mock_rag_google_service):
    """Test Google RAG query tool."""
    result = adk_agent_all_providers._rag_query_google_tool("test query")

    assert result == "Google answer"
    mock_rag_google_service.query.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_create_session(adk_agent_local_only):
    """Test session creation."""
    mock_session_service = Mock()
    mock_session_service.create_session = AsyncMock()
    adk_agent_local_only.session_service = mock_session_service

    session_id = await adk_agent_local_only.create_session("test_user")

    assert session_id is not None
    mock_session_service.create_session.assert_called_once()


@pytest.mark.asyncio
async def test_chat(adk_agent_local_only):
    """Test chat functionality."""
    mock_result = Mock()
    mock_message = Mock()
    mock_part = Mock()
    mock_part.text = "Response text"
    mock_message.parts = [mock_part]
    mock_result.messages = [mock_message]

    mock_runner = Mock()
    mock_runner.run = AsyncMock(return_value=mock_result)
    adk_agent_local_only.runner = mock_runner

    response = await adk_agent_local_only.chat(
        "Hello",
        "user123",
        "session123"
    )

    assert response == "Response text"
    mock_runner.run.assert_called_once()


@pytest.mark.asyncio
async def test_chat_no_response(adk_agent_local_only):
    """Test chat with no response."""
    mock_result = Mock()
    mock_result.messages = []

    mock_runner = Mock()
    mock_runner.run = AsyncMock(return_value=mock_result)
    adk_agent_local_only.runner = mock_runner

    response = await adk_agent_local_only.chat(
        "Hello",
        "user123",
        "session123"
    )

    assert response == "No response generated"


def test_instruction_content_local_only(mock_rag_service):
    """Test that instruction includes only local tool when no other providers."""
    with patch('app.services.adk_agent.LiteLlm'), \
            patch('app.services.adk_agent.LlmAgent') as mock_agent_class, \
            patch('app.services.adk_agent.Runner'):
        ADKAgentService(mock_rag_service)

        call_kwargs = mock_agent_class.call_args[1]
        instruction = call_kwargs['instruction']

        assert 'rag_query()' in instruction
        assert 'rag_query_anthropic()' not in instruction
        assert 'rag_query_google()' not in instruction


def test_instruction_content_all_providers(mock_rag_service, mock_rag_anthropic_service,
                                           mock_rag_google_service):
    """Test that instruction includes guidance for all providers."""
    with patch('app.services.adk_agent.LiteLlm'), \
            patch('app.services.adk_agent.LlmAgent') as mock_agent_class, \
            patch('app.services.adk_agent.Runner'):
        ADKAgentService(
            mock_rag_service,
            mock_rag_anthropic_service,
            mock_rag_google_service
        )

        call_kwargs = mock_agent_class.call_args[1]
        instruction = call_kwargs['instruction']

        # Check all tools are mentioned
        assert 'rag_query()' in instruction
        assert 'rag_query_anthropic()' in instruction
        assert 'rag_query_google()' in instruction

        # Check guidance for when to use each
        assert 'complex reasoning' in instruction.lower() or 'analysis' in instruction.lower()
        assert 'factual' in instruction.lower() or 'summaries' in instruction.lower()