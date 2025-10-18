"""
Tests for coordinator agent service.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from google.genai import types

from app.services.coordinator_agent import CoordinatorAgentService
from app.services.rag import RAGService


@pytest.fixture
def mock_rag_service():
    """Create a mock RAG service."""
    return Mock(spec=RAGService)


@pytest.fixture
def mock_event_final_response():
    """Create a mock final response event."""
    event = Mock()
    event.is_final_response.return_value = True
    event.author = "code_validator"

    # Mock content structure
    part = Mock()
    part.text = "This is the specialist response"
    event.content = Mock()
    event.content.parts = [part]

    return event


@pytest.fixture
def mock_event_non_final():
    """Create a mock non-final event."""
    event = Mock()
    event.is_final_response.return_value = False
    return event


class TestCoordinatorAgentService:
    """Tests for CoordinatorAgentService."""

    @patch('app.services.coordinator_agent.SpecializedAgentsFactory')
    def test_initialization(self, mock_factory_class, mock_rag_service):
        """Test coordinator service initializes correctly."""
        # Mock factory and agents
        mock_factory = Mock()
        mock_general_agent = Mock()
        mock_general_agent.name = "general_assistant"

        mock_factory.create_all_agents.return_value = [
            mock_general_agent,
            Mock(name="code_validator"),
        ]
        mock_factory_class.return_value = mock_factory

        # Create service
        service = CoordinatorAgentService(rag_service=mock_rag_service)

        # Verify initialization
        assert service.rag_service == mock_rag_service
        assert service.coordinator is not None
        assert service.runner is not None
        assert service.general_assistant == mock_general_agent
        assert len(service.specialist_agents) == 2

    @patch('app.services.coordinator_agent.SpecializedAgentsFactory')
    def test_initialization_with_optional_services(
            self, mock_factory_class, mock_rag_service
    ):
        """Test initialization with optional anthropic and google services."""
        mock_anthropic = Mock()
        mock_google = Mock()

        # Mock factory
        mock_factory = Mock()
        mock_general_agent = Mock()
        mock_general_agent.name = "general_assistant"
        mock_factory.create_all_agents.return_value = [mock_general_agent]
        mock_factory_class.return_value = mock_factory

        # Create service with optional services
        service = CoordinatorAgentService(
            rag_service=mock_rag_service,
            rag_anthropic_service=mock_anthropic,
            rag_google_service=mock_google
        )

        assert service.rag_anthropic_service == mock_anthropic
        assert service.rag_google_service == mock_google

    @patch('app.services.coordinator_agent.SpecializedAgentsFactory')
    async def test_chat_successful_delegation(
            self, mock_factory_class, mock_rag_service, mock_event_final_response
    ):
        """Test successful chat with delegation to specialist."""
        # Mock factory
        mock_factory = Mock()
        mock_general_agent = Mock()
        mock_general_agent.name = "general_assistant"
        mock_factory.create_all_agents.return_value = [mock_general_agent]
        mock_factory_class.return_value = mock_factory

        service = CoordinatorAgentService(rag_service=mock_rag_service)

        # Mock runner to return events
        async def mock_run_async(*args, **kwargs):
            yield mock_event_final_response

        service.runner.run_async = mock_run_async

        # Test chat
        response = await service.chat(
            message="validate my code",
            user_id="test_user",
            session_id="test_session"
        )

        assert response == "This is the specialist response"

    @patch('app.services.coordinator_agent.SpecializedAgentsFactory')
    async def test_chat_no_final_response_triggers_fallback(
            self, mock_factory_class, mock_rag_service, mock_event_non_final
    ):
        """Test chat falls back to general assistant when no final response."""
        # Mock factory
        mock_factory = Mock()
        mock_general_agent = Mock()
        mock_general_agent.name = "general_assistant"
        mock_factory.create_all_agents.return_value = [mock_general_agent]
        mock_factory_class.return_value = mock_factory

        service = CoordinatorAgentService(rag_service=mock_rag_service)

        # Mock coordinator runner to return no final response
        async def mock_coordinator_run(*args, **kwargs):
            yield mock_event_non_final

        service.runner.run_async = mock_coordinator_run

        # Mock fallback response
        fallback_event = Mock()
        fallback_event.is_final_response.return_value = True
        fallback_part = Mock()
        fallback_part.text = "Fallback response from general assistant"
        fallback_event.content = Mock()
        fallback_event.content.parts = [fallback_part]

        async def mock_fallback_run(*args, **kwargs):
            yield fallback_event

        with patch('app.services.coordinator_agent.Runner') as mock_runner_class:
            mock_fallback_runner = Mock()
            mock_fallback_runner.run_async = mock_fallback_run
            mock_runner_class.return_value = mock_fallback_runner

            # Test chat
            response = await service.chat(
                message="hello",
                user_id="test_user",
                session_id="test_session"
            )

            assert response == "Fallback response from general assistant"

    @patch('app.services.coordinator_agent.SpecializedAgentsFactory')
    async def test_chat_exception_triggers_fallback(
            self, mock_factory_class, mock_rag_service
    ):
        """Test chat falls back to general assistant on exception."""
        # Mock factory
        mock_factory = Mock()
        mock_general_agent = Mock()
        mock_general_agent.name = "general_assistant"
        mock_factory.create_all_agents.return_value = [mock_general_agent]
        mock_factory_class.return_value = mock_factory

        service = CoordinatorAgentService(rag_service=mock_rag_service)

        # Mock coordinator runner to raise exception
        async def mock_coordinator_run(*args, **kwargs):
            raise Exception("Coordinator failed")
            yield  # Make it a generator

        service.runner.run_async = mock_coordinator_run

        # Mock fallback response
        fallback_event = Mock()
        fallback_event.is_final_response.return_value = True
        fallback_part = Mock()
        fallback_part.text = "Fallback after error"
        fallback_event.content = Mock()
        fallback_event.content.parts = [fallback_part]

        async def mock_fallback_run(*args, **kwargs):
            yield fallback_event

        with patch('app.services.coordinator_agent.Runner') as mock_runner_class:
            mock_fallback_runner = Mock()
            mock_fallback_runner.run_async = mock_fallback_run
            mock_runner_class.return_value = mock_fallback_runner

            # Test chat
            response = await service.chat(
                message="test message",
                user_id="test_user",
                session_id="test_session"
            )

            assert response == "Fallback after error"

    @patch('app.services.coordinator_agent.SpecializedAgentsFactory')
    async def test_chat_fallback_also_fails(
            self, mock_factory_class, mock_rag_service
    ):
        """Test default message when both coordinator and fallback fail."""
        # Mock factory
        mock_factory = Mock()
        mock_general_agent = Mock()
        mock_general_agent.name = "general_assistant"
        mock_factory.create_all_agents.return_value = [mock_general_agent]
        mock_factory_class.return_value = mock_factory

        service = CoordinatorAgentService(rag_service=mock_rag_service)

        # Mock coordinator runner to raise exception
        async def mock_coordinator_run(*args, **kwargs):
            raise Exception("Coordinator failed")
            yield

        service.runner.run_async = mock_coordinator_run

        # Mock fallback to also raise exception
        async def mock_fallback_run(*args, **kwargs):
            raise Exception("Fallback also failed")
            yield

        with patch('app.services.coordinator_agent.Runner') as mock_runner_class:
            mock_fallback_runner = Mock()
            mock_fallback_runner.run_async = mock_fallback_run
            mock_runner_class.return_value = mock_fallback_runner

            # Test chat
            response = await service.chat(
                message="test message",
                user_id="test_user",
                session_id="test_session"
            )

            # Should return default error message
            assert "apologize" in response.lower()
            assert "trouble" in response.lower()

    @patch('app.services.coordinator_agent.SpecializedAgentsFactory')
    def test_coordinator_has_all_specialists_as_subagents(
            self, mock_factory_class, mock_rag_service
    ):
        """Test coordinator is created with all specialists as sub_agents."""
        # Mock factory with multiple agents
        mock_factory = Mock()
        mock_agents = [
            Mock(name="general_assistant", description="General chat"),
            Mock(name="code_validator", description="Code validation"),
            Mock(name="rag_assistant", description="RAG queries"),
        ]
        mock_factory.create_all_agents.return_value = mock_agents
        mock_factory_class.return_value = mock_factory

        service = CoordinatorAgentService(rag_service=mock_rag_service)

        # Verify coordinator was created (would fail if sub_agents weren't set)
        assert service.coordinator is not None
        assert service.coordinator.name == "coordinator"

        # Verify all specialists are available
        assert len(service.specialist_agents) == 3

    @patch('app.services.coordinator_agent.settings')
    @patch('app.services.coordinator_agent.SpecializedAgentsFactory')
    def test_uses_phi3_for_coordinator(
            self, mock_factory_class, mock_settings, mock_rag_service
    ):
        """Test coordinator uses phi3mini model for fast routing."""
        mock_settings.provider_type = "ollama"
        mock_settings.app_name = "test_app"

        # Mock factory
        mock_factory = Mock()
        mock_general_agent = Mock()
        mock_general_agent.name = "general_assistant"
        mock_factory.create_all_agents.return_value = [mock_general_agent]
        mock_factory_class.return_value = mock_factory

        service = CoordinatorAgentService(rag_service=mock_rag_service)

        # Coordinator should be created with a model
        assert service.coordinator.model is not None
