"""
Tests for specialized agents factory.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from app.services.specialized_agents import SpecializedAgentsFactory
from app.services.rag import RAGService
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService


@pytest.fixture
def mock_rag_service():
    """Create a mock RAG service."""
    service = Mock(spec=RAGService)
    return service


@pytest.fixture
def mock_rag_anthropic_service():
    """Create a mock Anthropic RAG service."""
    service = Mock(spec=RAGAnthropicService)
    return service


@pytest.fixture
def mock_rag_google_service():
    """Create a mock Google RAG service."""
    service = Mock(spec=RAGGoogleService)
    return service


@pytest.fixture
def factory_with_all_services(mock_rag_service, mock_rag_anthropic_service, mock_rag_google_service):
    """Create factory with all services."""
    with patch('app.services.specialized_agents.create_rag_tools') as mock_create_tools:
        # Mock RAG tools
        mock_create_tools.return_value = [
            MagicMock(name='rag_query'),
            MagicMock(name='rag_query_anthropic'),
            MagicMock(name='rag_query_google')
        ]

        factory = SpecializedAgentsFactory(
            rag_service=mock_rag_service,
            rag_anthropic_service=mock_rag_anthropic_service,
            rag_google_service=mock_rag_google_service
        )
        return factory


@pytest.fixture
def factory_basic(mock_rag_service):
    """Create factory with only basic RAG service."""
    with patch('app.services.specialized_agents.create_rag_tools') as mock_create_tools:
        # Mock single RAG tool
        mock_create_tools.return_value = [MagicMock(name='rag_query')]

        factory = SpecializedAgentsFactory(
            rag_service=mock_rag_service,
            rag_anthropic_service=None,
            rag_google_service=None
        )
        return factory


class TestSpecializedAgentsFactory:
    """Tests for SpecializedAgentsFactory."""

    def test_factory_initialization(self, factory_with_all_services):
        """Test factory initializes correctly."""
        assert factory_with_all_services.rag_service is not None
        assert factory_with_all_services.rag_anthropic_service is not None
        assert factory_with_all_services.rag_google_service is not None
        assert factory_with_all_services.phi3_model is not None
        assert factory_with_all_services.mistral_model is not None
        assert len(factory_with_all_services.rag_tools) == 3

    def test_factory_initialization_basic(self, factory_basic):
        """Test factory initializes with minimal services."""
        assert factory_basic.rag_service is not None
        assert factory_basic.rag_anthropic_service is None
        assert factory_basic.rag_google_service is None
        assert len(factory_basic.rag_tools) == 1

    def test_create_code_validation_agent(self, factory_basic):
        """Test code validation agent creation."""
        agent = factory_basic.create_code_validation_agent()

        assert agent.name == "code_validator"
        assert agent.description is not None
        assert "validates" in agent.description.lower()
        assert agent.instruction is not None
        assert len(agent.tools) == 1  # validate_code only
        assert agent.model is not None

    def test_create_rag_query_agent(self, factory_with_all_services):
        """Test RAG query agent creation."""
        agent = factory_with_all_services.create_rag_query_agent()

        assert agent.name == "rag_assistant"
        assert "knowledge base" in agent.description.lower()
        assert agent.instruction is not None
        assert len(agent.tools) == 3  # All RAG tools
        assert agent.model is not None

    def test_create_rag_query_agent_basic(self, factory_basic):
        """Test RAG query agent with only basic RAG service."""
        agent = factory_basic.create_rag_query_agent()

        assert agent.name == "rag_assistant"
        assert len(agent.tools) == 1  # Only basic rag_query

    def test_create_code_generation_agent(self, factory_basic):
        """Test code generation agent creation."""
        agent = factory_basic.create_code_generation_agent()

        assert agent.name == "code_generator"
        assert "generates" in agent.description.lower()
        assert agent.instruction is not None
        assert len(agent.tools) == 1  # validate_code only
        assert agent.model is not None

    def test_create_code_analysis_agent(self, factory_with_all_services):
        """Test code analysis agent creation."""
        agent = factory_with_all_services.create_code_analysis_agent()

        assert agent.name == "code_analyst"
        assert "analyzes" in agent.description.lower()
        assert agent.instruction is not None
        assert len(agent.tools) == 4  # validate_code + 3 RAG tools
        assert agent.model is not None

    def test_create_complex_reasoning_agent(self, factory_with_all_services):
        """Test complex reasoning agent creation."""
        agent = factory_with_all_services.create_complex_reasoning_agent()

        assert agent.name == "complex_reasoner"
        assert "complex" in agent.description.lower()
        assert agent.instruction is not None
        assert len(agent.tools) == 4  # All tools: validate_code + 3 RAG tools
        assert agent.model is not None

    def test_create_general_chat_agent(self, factory_basic):
        """Test general chat agent creation."""
        agent = factory_basic.create_general_chat_agent()

        assert agent.name == "general_assistant"
        assert "conversation" in agent.description.lower()
        assert agent.instruction is not None
        assert len(agent.tools) == 0  # No tools for speed
        assert agent.model is not None

    def test_create_all_agents(self, factory_with_all_services):
        """Test creating all agents at once."""
        agents = factory_with_all_services.create_all_agents()

        assert len(agents) == 6

        # Verify agent names
        agent_names = [agent.name for agent in agents]
        expected_names = [
            "code_validator",
            "rag_assistant",
            "code_generator",
            "code_analyst",
            "complex_reasoner",
            "general_assistant"
        ]
        assert agent_names == expected_names

    def test_all_agents_have_required_fields(self, factory_basic):
        """Test all agents have required ADK fields."""
        agents = factory_basic.create_all_agents()

        for agent in agents:
            # All agents must have these fields
            assert agent.name is not None
            assert isinstance(agent.name, str)
            assert len(agent.name) > 0

            assert agent.description is not None
            assert isinstance(agent.description, str)
            assert len(agent.description) > 0

            assert agent.instruction is not None
            assert isinstance(agent.instruction, str)
            assert len(agent.instruction) > 0

            assert agent.model is not None

            # Tools can be empty list but must exist
            assert agent.tools is not None
            assert isinstance(agent.tools, list)

    def test_agent_tool_distribution(self, factory_with_all_services):
        """Test correct tool distribution across agents."""
        agents = {
            agent.name: agent
            for agent in factory_with_all_services.create_all_agents()
        }

        # Code validator: validate_code only
        assert len(agents["code_validator"].tools) == 1

        # RAG assistant: all RAG tools
        assert len(agents["rag_assistant"].tools) == 3

        # Code generator: validate_code only
        assert len(agents["code_generator"].tools) == 1

        # Code analyst: validate_code + all RAG tools
        assert len(agents["code_analyst"].tools) == 4

        # Complex reasoner: all tools
        assert len(agents["complex_reasoner"].tools) == 4

        # General assistant: no tools
        assert len(agents["general_assistant"].tools) == 0

    def test_model_assignment(self, factory_with_all_services):
        """Test correct model assignment (phi3 vs mistral)."""
        agents = {
            agent.name: agent
            for agent in factory_with_all_services.create_all_agents()
        }

        # These should use phi3 (faster)
        phi3_agents = [
            "code_validator",
            "rag_assistant",
            "code_generator",
            "general_assistant"
        ]

        # These should use mistral (more complex)
        mistral_agents = [
            "code_analyst",
            "complex_reasoner"
        ]

        for agent_name in phi3_agents:
            assert agents[agent_name].model == factory_with_all_services.phi3_model

        for agent_name in mistral_agents:
            assert agents[agent_name].model == factory_with_all_services.mistral_model

    def test_agent_descriptions_unique(self, factory_basic):
        """Test all agents have unique, descriptive descriptions."""
        agents = factory_basic.create_all_agents()
        descriptions = [agent.description for agent in agents]

        # All descriptions should be unique
        assert len(descriptions) == len(set(descriptions))

        # All descriptions should be reasonably long
        for desc in descriptions:
            assert len(desc) > 20

    def test_agent_names_unique(self, factory_basic):
        """Test all agents have unique names."""
        agents = factory_basic.create_all_agents()
        names = [agent.name for agent in agents]

        # All names should be unique
        assert len(names) == len(set(names))

    @patch('app.services.specialized_agents.settings')
    def test_ollama_model_creation(self, mock_settings, mock_rag_service):
        """Test model creation for Ollama provider."""
        mock_settings.provider_type = "ollama"
        mock_settings.llama_server_host = "localhost"
        mock_settings.llama_server_port = 8080

        with patch('app.services.specialized_agents.create_rag_tools') as mock_create_tools:
            mock_create_tools.return_value = []

            factory = SpecializedAgentsFactory(rag_service=mock_rag_service)

            # Check phi3 model
            assert "ollama_chat" in factory.phi3_model.model
            assert "phi3" in factory.phi3_model.model

            # Check mistral model
            assert "ollama_chat" in factory.mistral_model.model
            assert "mistral" in factory.mistral_model.model

    @patch('app.services.specialized_agents.settings')
    def test_llamacpp_model_creation(self, mock_settings, mock_rag_service):
        """Test model creation for llama.cpp provider."""
        mock_settings.provider_type = "llamacpp"
        mock_settings.llama_server_host = "127.0.0.1"
        mock_settings.llama_server_port = 8080

        with patch('app.services.specialized_agents.create_rag_tools') as mock_create_tools:
            mock_create_tools.return_value = []

            factory = SpecializedAgentsFactory(rag_service=mock_rag_service)

            # Both should use llama-server
            assert factory.phi3_model.api_base is not None
            assert "8080" in factory.phi3_model.api_base
            assert factory.mistral_model.api_base is not None