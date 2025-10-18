"""
Integration tests for router with application.

Run with: pytest tests/test_integration.py -v
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.core.application import RAGAgentApp


class TestApplicationRouterIntegration:
    """Test router integration with RAGAgentApp."""

    @pytest.fixture
    def mock_services(self):
        """Mock all service dependencies."""
        with patch('app.core.application.VectorStoreService') as mock_vs, \
                patch('app.core.application.RAGService') as mock_rag, \
                patch('app.core.application.ADKAgentService') as mock_adk, \
                patch('app.core.application.RouterService') as mock_router:
            # Setup mock returns
            mock_router_instance = MagicMock()
            mock_router_instance.enabled = True
            mock_router.return_value = mock_router_instance

            yield {
                'vector_store': mock_vs,
                'rag': mock_rag,
                'adk': mock_adk,
                'router': mock_router,
                'router_instance': mock_router_instance
            }

    def test_application_initializes_router(self, mock_services):
        """Application should initialize router on startup."""
        app = RAGAgentApp()

        mock_services['router'].assert_called_once()
        assert hasattr(app, 'router')

    @pytest.mark.asyncio
    async def test_chat_routes_when_enabled(self, mock_services):
        """Chat should use router when enabled."""
        mock_services['router_instance'].enabled = True
        mock_services['router_instance'].route.return_value = {
            'primary_agent': 'code_generation',
            'parallel_agents': [],
            'confidence': 0.95,
            'reasoning': 'Test routing'
        }

        # Mock ADK agent response
        mock_adk_instance = MagicMock()
        mock_adk_instance.chat = AsyncMock(return_value="Generated code")
        mock_services['adk'].return_value = mock_adk_instance

        app = RAGAgentApp()

        response = await app.chat(
            message="Write a function",
            user_id="test",
            session_id="123"
        )

        # Should have called router
        mock_services['router_instance'].route.assert_called_once_with("Write a function")

        # Should return string response
        assert isinstance(response, str)
        assert response == "Generated code"

    @pytest.mark.asyncio
    async def test_chat_skips_routing_when_disabled(self, mock_services):
        """Chat should skip routing when router disabled."""
        mock_services['router_instance'].enabled = False

        # Mock ADK agent response
        mock_adk_instance = MagicMock()
        mock_adk_instance.chat = AsyncMock(return_value="Response")
        mock_services['adk'].return_value = mock_adk_instance

        app = RAGAgentApp()

        response = await app.chat(
            message="Test message",
            user_id="test",
            session_id="123"
        )

        # Router should not be called
        mock_services['router_instance'].route.assert_not_called()

        # Should still return response
        assert response == "Response"

    @pytest.mark.asyncio
    async def test_chat_handles_routing_failure(self, mock_services):
        """Chat should continue if routing fails."""
        mock_services['router_instance'].enabled = True
        mock_services['router_instance'].route.side_effect = Exception("Routing failed")

        # Mock ADK agent response
        mock_adk_instance = MagicMock()
        mock_adk_instance.chat = AsyncMock(return_value="Response")
        mock_services['adk'].return_value = mock_adk_instance

        app = RAGAgentApp()

        # Should not raise, should continue
        response = await app.chat(
            message="Test",
            user_id="test",
            session_id="123"
        )

        assert response == "Response"

    @pytest.mark.asyncio
    async def test_get_last_routing_returns_decision(self, mock_services):
        """get_last_routing should return routing decision from last chat."""
        mock_services['router_instance'].enabled = True
        routing_decision = {
            'primary_agent': 'code_validation',
            'parallel_agents': [],
            'confidence': 0.92,
            'reasoning': 'Test'
        }
        mock_services['router_instance'].route.return_value = routing_decision

        # Mock ADK agent
        mock_adk_instance = MagicMock()
        mock_adk_instance.chat = AsyncMock(return_value="Response")
        mock_services['adk'].return_value = mock_adk_instance

        app = RAGAgentApp()

        await app.chat(
            message="Validate code",
            user_id="test",
            session_id="123"
        )

        last_routing = app.get_last_routing()

        assert last_routing is not None
        assert last_routing['primary_agent'] == 'code_validation'
        assert last_routing['confidence'] == 0.92

    @pytest.mark.asyncio
    async def test_get_last_routing_returns_none_when_disabled(self, mock_services):
        """get_last_routing should return None when router disabled."""
        mock_services['router_instance'].enabled = False

        # Mock ADK agent
        mock_adk_instance = MagicMock()
        mock_adk_instance.chat = AsyncMock(return_value="Response")
        mock_services['adk'].return_value = mock_adk_instance

        app = RAGAgentApp()

        await app.chat(
            message="Test",
            user_id="test",
            session_id="123"
        )

        last_routing = app.get_last_routing()
        assert last_routing is None

    def test_get_stats_includes_router_info(self, mock_services):
        """get_stats should include router status."""
        mock_services['router_instance'].enabled = True

        with patch('app.core.application.settings') as mock_settings:
            mock_settings.provider_type = 'ollama'
            mock_settings.collection_name = 'test'
            mock_settings.router_model_path = '/path/to/model.gguf'

            # Mock vector store
            mock_collection = MagicMock()
            mock_collection.count.return_value = 42
            mock_vs_instance = MagicMock()
            mock_vs_instance.get_collection.return_value = mock_collection
            mock_services['vector_store'].return_value = mock_vs_instance

            app = RAGAgentApp()
            stats = app.get_stats()

            assert stats['router_enabled'] is True
            assert stats['router_model'] == '/path/to/model.gguf'


class TestAPIEndpointIntegration:
    """Test API endpoints with router."""

    @pytest.mark.asyncio
    async def test_chat_endpoint_backwards_compatible(self):
        """POST /chat should return response without routing_info by default."""
        from app.api.main import app as fastapi_app
        from httpx import AsyncClient

        with patch('app.api.main.rag_app') as mock_app:
            mock_app.chat = AsyncMock(return_value="Test response")

            async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
                response = await client.post(
                    "/chat",
                    json={
                        "message": "Test",
                        "user_id": "test",
                        "session_id": "123"
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data['response'] == "Test response"
                assert data['session_id'] == "123"
                assert data['routing_info'] is None  # Backwards compatible

    @pytest.mark.asyncio
    async def test_chat_extended_endpoint_includes_routing(self):
        """POST /chat/extended should include routing_info when available."""
        from app.api.main import app as fastapi_app
        from httpx import AsyncClient

        with patch('app.api.main.rag_app') as mock_app:
            mock_app.chat = AsyncMock(return_value="Test response")
            mock_app.get_last_routing.return_value = {
                'primary_agent': 'code_generation',
                'confidence': 0.95,
                'reasoning': 'Test'
            }

            async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
                response = await client.post(
                    "/chat/extended",
                    json={
                        "message": "Write code",
                        "user_id": "test",
                        "session_id": "123"
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data['response'] == "Test response"
                assert data['routing_info'] is not None
                assert data['routing_info']['agent'] == 'code_generation'

    @pytest.mark.asyncio
    async def test_stats_endpoint_shows_router_status(self):
        """GET /stats should include router information."""
        from app.api.main import app as fastapi_app
        from httpx import AsyncClient

        with patch('app.api.main.rag_app') as mock_app:
            mock_app.get_stats.return_value = {
                'provider_type': 'ollama',
                'vector_store_collection': 'test',
                'document_count': 10,
                'router_enabled': True,
                'router_model': '/path/to/model.gguf'
            }

            async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
                response = await client.get("/stats")

                assert response.status_code == 200
                data = response.json()
                assert data['router_enabled'] is True
                assert 'router_model' in data