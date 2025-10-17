"""
Integration tests for ADK Agent service with refactored tools.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.adk_agent import ADKAgentService


class TestADKAgentServiceInitialization:
    """Tests for ADKAgentService initialization."""

    @patch('app.services.adk_agent.settings')
    def test_init_with_only_local_rag(self, mock_settings):
        """Test initialization with only local RAG service."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()

        service = ADKAgentService(rag_service=mock_rag)

        assert service.rag_service == mock_rag
        assert service.rag_anthropic_service is None
        assert service.rag_google_service is None
        assert service.agent is not None

    @patch('app.services.adk_agent.settings')
    def test_init_with_all_providers(self, mock_settings):
        """Test initialization with all RAG providers."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        mock_anthropic = Mock()
        mock_google = Mock()

        service = ADKAgentService(
            rag_service=mock_rag,
            rag_anthropic_service=mock_anthropic,
            rag_google_service=mock_google
        )

        assert service.rag_service == mock_rag
        assert service.rag_anthropic_service == mock_anthropic
        assert service.rag_google_service == mock_google


class TestADKAgentToolBuilding:
    """Tests for tool building logic."""

    @patch('app.services.adk_agent.settings')
    @patch('app.services.adk_agent.create_rag_tools')
    def test_build_tools_includes_validation(self, mock_create_rag_tools, mock_settings):
        """Test that validation tool is included."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        mock_create_rag_tools.return_value = [Mock()]

        service = ADKAgentService(rag_service=mock_rag)
        tools = service._build_tools()

        # Should have validation tool + RAG tools
        assert len(tools) >= 2
        # First tool should be validate_code
        assert tools[0].__name__ == 'validate_code'

    @patch('app.services.adk_agent.settings')
    @patch('app.services.adk_agent.create_rag_tools')
    def test_build_tools_calls_create_rag_tools(self, mock_create_rag_tools, mock_settings):
        """Test that create_rag_tools is called with correct services."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        mock_anthropic = Mock()
        mock_google = Mock()
        mock_create_rag_tools.return_value = [Mock(), Mock(), Mock()]

        service = ADKAgentService(
            rag_service=mock_rag,
            rag_anthropic_service=mock_anthropic,
            rag_google_service=mock_google
        )

        service._build_tools()

        mock_create_rag_tools.assert_called_once_with(
            rag_service=mock_rag,
            rag_anthropic_service=mock_anthropic,
            rag_google_service=mock_google
        )


class TestADKAgentInstructions:
    """Tests for instruction building."""

    @patch('app.services.adk_agent.settings')
    def test_instruction_with_tools_includes_validation(self, mock_settings):
        """Test instruction mentions validation tool."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        service = ADKAgentService(rag_service=mock_rag)

        instruction = service._build_instruction_with_tools()

        assert 'validate_code' in instruction
        assert 'rag_query' in instruction

    @patch('app.services.adk_agent.settings')
    def test_instruction_with_anthropic_mentions_it(self, mock_settings):
        """Test instruction mentions Anthropic when available."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        mock_anthropic = Mock()

        service = ADKAgentService(
            rag_service=mock_rag,
            rag_anthropic_service=mock_anthropic
        )

        instruction = service._build_instruction_with_tools()

        assert 'rag_query_anthropic' in instruction
        assert 'complex reasoning' in instruction.lower() or 'anthropic' in instruction.lower()

    @patch('app.services.adk_agent.settings')
    def test_instruction_with_google_mentions_it(self, mock_settings):
        """Test instruction mentions Google when available."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        mock_google = Mock()

        service = ADKAgentService(
            rag_service=mock_rag,
            rag_google_service=mock_google
        )

        instruction = service._build_instruction_with_tools()

        assert 'rag_query_google' in instruction

    @patch('app.services.adk_agent.settings')
    def test_instruction_without_tools_is_simple(self, mock_settings):
        """Test instruction without tools is basic."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        service = ADKAgentService(rag_service=mock_rag)

        instruction = service._build_instruction_without_tools()

        assert 'helpful assistant' in instruction.lower()
        assert 'validate_code' not in instruction
        assert 'rag_query' not in instruction


class TestADKAgentProviderConfiguration:
    """Tests for provider-specific configuration."""

    @patch('app.services.adk_agent.settings')
    @patch('app.services.adk_agent.LiteLlm')
    def test_configure_ollama(self, mock_lite_llm, mock_settings):
        """Test Ollama configuration."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        service = ADKAgentService(rag_service=mock_rag)

        llm, tools_enabled = service._configure_ollama()

        assert tools_enabled is True
        assert mock_lite_llm.called

    @patch('app.services.adk_agent.settings')
    @patch('app.services.adk_agent.LiteLlm')
    @patch('app.services.adk_agent.requests')
    def test_configure_llamacpp_server_available(self, mock_requests, mock_lite_llm, mock_settings):
        """Test llama.cpp configuration when server is available."""
        mock_settings.provider_type = 'llamacpp'
        mock_settings.llama_server_host = 'localhost'
        mock_settings.llama_server_port = 8080
        mock_settings.app_name = 'test_app'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        mock_rag = Mock()
        service = ADKAgentService(rag_service=mock_rag)

        llm, tools_enabled = service._configure_llamacpp()

        assert tools_enabled is True

    @patch('app.services.adk_agent.settings')
    @patch('app.services.adk_agent.LiteLlm')
    @patch('app.services.adk_agent.requests')
    def test_configure_llamacpp_server_unavailable(self, mock_requests, mock_lite_llm, mock_settings):
        """Test llama.cpp configuration when server is unavailable."""
        mock_settings.provider_type = 'llamacpp'
        mock_settings.llama_server_host = 'localhost'
        mock_settings.llama_server_port = 8080
        mock_settings.app_name = 'test_app'

        mock_requests.get.side_effect = Exception("Connection refused")

        mock_rag = Mock()
        service = ADKAgentService(rag_service=mock_rag)

        llm, tools_enabled = service._configure_llamacpp()

        assert tools_enabled is False


class TestADKAgentSessionManagement:
    """Tests for session management."""

    @pytest.mark.asyncio
    @patch('app.services.adk_agent.settings')
    async def test_create_session(self, mock_settings):
        """Test session creation."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        service = ADKAgentService(rag_service=mock_rag)

        session_id = await service.create_session("test_user")

        assert isinstance(session_id, str)
        assert len(session_id) > 0


class TestToolsImportIntegration:
    """Tests to ensure tools are properly imported and used."""

    def test_validate_code_imported(self):
        """Test that validate_code is properly imported."""
        from app.tools import validate_code
        assert callable(validate_code)

    def test_create_rag_tools_imported(self):
        """Test that create_rag_tools is properly imported."""
        from app.tools import create_rag_tools
        assert callable(create_rag_tools)

    @patch('app.services.adk_agent.settings')
    def test_adk_service_uses_imported_tools(self, mock_settings):
        """Test that ADKAgentService uses the imported tools."""
        mock_settings.provider_type = 'ollama'
        mock_settings.chat_model = 'llama2'
        mock_settings.app_name = 'test_app'

        mock_rag = Mock()
        service = ADKAgentService(rag_service=mock_rag)

        # The service should have been created successfully
        assert service.agent is not None

        # Build tools to verify they're using the imported functions
        tools = service._build_tools()
        assert len(tools) > 0