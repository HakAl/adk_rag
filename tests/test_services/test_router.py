"""
Tests for RouterService.

Run with: pytest tests/test_router.py -v
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.services.router import RouterService


class TestRouterInitialization:
    """Test router initialization and configuration."""

    def test_router_disabled_when_no_model_path(self):
        """Router should be disabled when ROUTER_MODEL_PATH not configured."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = None
            mock_settings.debug = False

            router = RouterService()

            assert router.enabled is False
            assert router.llm is None

    def test_router_disabled_when_model_path_not_exists(self):
        """Router should be disabled when model file doesn't exist."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = "/nonexistent/model.gguf"
            mock_settings.debug = False

            router = RouterService()

            assert router.enabled is False

    def test_router_enabled_when_model_path_exists(self):
        """Router should be enabled when valid model path configured."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = "/fake/model.gguf"
            mock_settings.router_n_ctx = 2048
            mock_settings.router_n_batch = 512
            mock_settings.router_n_threads = None
            mock_settings.router_temperature = 0.3
            mock_settings.debug = False

            with patch('pathlib.Path.exists', return_value=True):
                with patch('app.services.router.Llama') as mock_llama:
                    router = RouterService()

                    assert router.enabled is True
                    assert router.llm is not None
                    mock_llama.assert_called_once()


class TestRouterClassification:
    """Test router request classification."""

    @pytest.fixture
    def mock_router(self):
        """Create a mock router with enabled flag."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = "/fake/model.gguf"
            mock_settings.router_n_ctx = 2048
            mock_settings.router_n_batch = 512
            mock_settings.router_n_threads = None
            mock_settings.router_temperature = 0.3
            mock_settings.router_max_tokens = 256
            mock_settings.debug = False

            with patch('pathlib.Path.exists', return_value=True):
                with patch('app.services.router.Llama'):
                    router = RouterService()
                    router.enabled = True
                    router.llm = MagicMock()
                    return router

    def test_route_code_validation(self, mock_router):
        """Should route code validation requests correctly."""
        mock_router.llm.return_value = {
            'choices': [{
                'text': '''{
                    "primary_agent": "code_validation",
                    "parallel_agents": [],
                    "confidence": 0.95,
                    "reasoning": "User wants code syntax validation"
                }'''
            }]
        }

        result = mock_router.route("Can you validate this Python code: print('hello')")

        assert result['primary_agent'] == 'code_validation'
        assert result['confidence'] >= 0.9
        assert isinstance(result['parallel_agents'], list)

    def test_route_rag_query(self, mock_router):
        """Should route knowledge base queries correctly."""
        mock_router.llm.return_value = {
            'choices': [{
                'text': '''{
                    "primary_agent": "rag_query",
                    "parallel_agents": [],
                    "confidence": 0.92,
                    "reasoning": "Question requires knowledge base lookup"
                }'''
            }]
        }

        result = mock_router.route("What does the documentation say about authentication?")

        assert result['primary_agent'] == 'rag_query'
        assert result['confidence'] > 0.5

    def test_route_code_generation(self, mock_router):
        """Should route code generation requests correctly."""
        mock_router.llm.return_value = {
            'choices': [{
                'text': '''{
                    "primary_agent": "code_generation",
                    "parallel_agents": [],
                    "confidence": 0.98,
                    "reasoning": "User wants new code written"
                }'''
            }]
        }

        result = mock_router.route(
            "Write a function to merge k sorted linked lists"
        )

        assert result['primary_agent'] == 'code_generation'
        assert result['confidence'] >= 0.9

    def test_route_code_analysis(self, mock_router):
        """Should route code analysis requests correctly."""
        mock_router.llm.return_value = {
            'choices': [{
                'text': '''{
                    "primary_agent": "code_analysis",
                    "parallel_agents": [],
                    "confidence": 0.90,
                    "reasoning": "User wants code explanation"
                }'''
            }]
        }

        result = mock_router.route("Explain how this quicksort implementation works")

        assert result['primary_agent'] == 'code_analysis'

    def test_route_complex_reasoning(self, mock_router):
        """Should route complex problems correctly."""
        mock_router.llm.return_value = {
            'choices': [{
                'text': '''{
                    "primary_agent": "complex_reasoning",
                    "parallel_agents": [],
                    "confidence": 0.88,
                    "reasoning": "Multi-step algorithmic problem"
                }'''
            }]
        }

        result = mock_router.route(
            "Design a distributed cache system with LRU eviction"
        )

        assert result['primary_agent'] == 'complex_reasoning'

    def test_route_general_chat(self, mock_router):
        """Should route casual conversation correctly."""
        mock_router.llm.return_value = {
            'choices': [{
                'text': '''{
                    "primary_agent": "general_chat",
                    "parallel_agents": [],
                    "confidence": 0.99,
                    "reasoning": "Casual greeting"
                }'''
            }]
        }

        result = mock_router.route("Hello! How are you today?")

        assert result['primary_agent'] == 'general_chat'


class TestRouterErrorHandling:
    """Test router error handling and fallbacks."""

    @pytest.fixture
    def mock_router_disabled(self):
        """Create a disabled router."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = None
            mock_settings.debug = False

            router = RouterService()
            return router

    def test_route_when_disabled_returns_default(self, mock_router_disabled):
        """Should return general_chat when router is disabled."""
        result = mock_router_disabled.route("Any message")

        assert result['primary_agent'] == 'general_chat'
        assert result['confidence'] == 1.0
        assert 'disabled' in result['reasoning'].lower()

    def test_route_handles_invalid_json(self):
        """Should handle invalid JSON response gracefully."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = "/fake/model.gguf"
            mock_settings.router_n_ctx = 2048
            mock_settings.router_n_batch = 512
            mock_settings.router_n_threads = None
            mock_settings.router_temperature = 0.3
            mock_settings.router_max_tokens = 256
            mock_settings.debug = False

            with patch('pathlib.Path.exists', return_value=True):
                with patch('app.services.router.Llama'):
                    router = RouterService()
                    router.enabled = True
                    router.llm = MagicMock()
                    router.llm.return_value = {
                        'choices': [{'text': 'not valid json'}]
                    }

                    result = router.route("test message")

                    # Should fallback to general_chat
                    assert result['primary_agent'] == 'general_chat'
                    assert result['confidence'] == 0.5

    def test_route_handles_missing_fields(self):
        """Should handle missing required fields in response."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = "/fake/model.gguf"
            mock_settings.router_n_ctx = 2048
            mock_settings.router_n_batch = 512
            mock_settings.router_n_threads = None
            mock_settings.router_temperature = 0.3
            mock_settings.router_max_tokens = 256
            mock_settings.debug = False

            with patch('pathlib.Path.exists', return_value=True):
                with patch('app.services.router.Llama'):
                    router = RouterService()
                    router.enabled = True
                    router.llm = MagicMock()
                    router.llm.return_value = {
                        'choices': [{
                            'text': '{"primary_agent": "code_validation"}'  # Missing fields
                        }]
                    }

                    result = router.route("test")

                    assert result['primary_agent'] == 'general_chat'

    def test_route_validates_agent_category(self):
        """Should validate agent category and default to general_chat for invalid."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = "/fake/model.gguf"
            mock_settings.router_n_ctx = 2048
            mock_settings.router_n_batch = 512
            mock_settings.router_n_threads = None
            mock_settings.router_temperature = 0.3
            mock_settings.router_max_tokens = 256
            mock_settings.debug = False

            with patch('pathlib.Path.exists', return_value=True):
                with patch('app.services.router.Llama'):
                    router = RouterService()
                    router.enabled = True
                    router.llm = MagicMock()
                    router.llm.return_value = {
                        'choices': [{
                            'text': '''{
                                "primary_agent": "invalid_agent_type",
                                "parallel_agents": [],
                                "confidence": 0.9,
                                "reasoning": "test"
                            }'''
                        }]
                    }

                    result = router.route("test")

                    assert result['primary_agent'] == 'general_chat'


class TestRouterUtilities:
    """Test router utility functions."""

    def test_get_agent_description_all_types(self):
        """Should return description for all valid agent types."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = None
            mock_settings.debug = False

            router = RouterService()

            agent_types = [
                "code_validation",
                "rag_query",
                "code_generation",
                "code_analysis",
                "complex_reasoning",
                "general_chat"
            ]

            for agent_type in agent_types:
                description = router.get_agent_description(agent_type)
                assert isinstance(description, str)
                assert len(description) > 0

    def test_get_agent_description_invalid_type(self):
        """Should return unknown message for invalid agent type."""
        with patch('app.services.router.settings') as mock_settings:
            mock_settings.router_model_path = None
            mock_settings.debug = False

            router = RouterService()

            description = router.get_agent_description("invalid_type")
            assert "unknown" in description.lower()