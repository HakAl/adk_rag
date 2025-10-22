"""
Main application class integrating all services with optional routing and coordination.
"""
from typing import Optional, Dict, Any, AsyncGenerator

from config import settings, logger
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService
from app.services.adk_agent import ADKAgentService
from app.services.coordinator_agent import CoordinatorAgentService


class RAGAgentApp:
    """Main application integrating vector store, RAG, and agent services."""

    def __init__(self):
        """Initialize application with all services."""
        logger.info("Initializing RAG Agent Application")

        # Only initialize vector store if we have local models configured
        self.vector_store = None
        self.rag_service = None

        if settings.provider_type in ['ollama', 'llamacpp']:
            try:
                # Check if provider is actually available
                if settings.provider_type == 'ollama':
                    logger.info("Attempting to initialize Ollama-based vector store...")
                elif settings.provider_type == 'llamacpp' and settings.llamacpp_embedding_model_path:
                    logger.info("Attempting to initialize llama.cpp-based vector store...")
                else:
                    logger.warning("Local provider configured but models not available, skipping vector store")

                if settings.provider_type == 'ollama' or (settings.provider_type == 'llamacpp' and settings.llamacpp_embedding_model_path):
                    from app.services.vector_store import VectorStoreService
                    from app.services.rag import RAGService

                    self.vector_store = VectorStoreService()
                    self.rag_service = RAGService(self.vector_store)
                    logger.info("Vector store and RAG service enabled")
            except Exception as e:
                logger.warning(f"Vector store initialization failed: {e}")
                logger.info("Continuing without local vector store - using cloud providers only")
                self.vector_store = None
                self.rag_service = None
        else:
            logger.info(f"Provider type '{settings.provider_type}' - skipping vector store initialization")

        self.rag_anthropic_service = None
        self.rag_google_service = None

        try:
            import os
            if os.getenv("ANTHROPIC_API_KEY"):
                self.rag_anthropic_service = RAGAnthropicService(self.vector_store)
                logger.info("✓ Anthropic RAG service enabled")
        except Exception as e:
            logger.warning(f"Anthropic RAG service not available: {e}")

        try:
            import os
            if os.getenv("GOOGLE_API_KEY"):
                self.rag_google_service = RAGGoogleService(self.vector_store)
                logger.info("✓ Google RAG service enabled")
        except Exception as e:
            logger.warning(f"Google RAG service not available: {e}")

        # Verify we have at least one service available
        if not any([self.rag_service, self.rag_anthropic_service, self.rag_google_service]):
            logger.error("No RAG services available! Set ANTHROPIC_API_KEY or GOOGLE_API_KEY")
            raise RuntimeError("No RAG services configured")

        self.adk_agent = ADKAgentService(
            rag_service=self.rag_service,
            rag_anthropic_service=self.rag_anthropic_service,
            rag_google_service=self.rag_google_service
        )
        logger.info("✓ ADK Agent service initialized")

        # Router is optional - only for local routing
        self.router = None
        try:
            from app.services.router import RouterService
            self.router = RouterService()

            if self.router.enabled:
                logger.info("✓ Router service enabled")
            else:
                logger.info("✗ Router service disabled")
        except Exception as e:
            logger.info(f"Router service not available: {e}")

        self.coordinator_agent = None
        if settings.use_coordinator_agent:
            if not self.router or not self.router.enabled:
                logger.warning("Coordinator agent requires router - disabling coordinator")
            else:
                try:
                    self.coordinator_agent = CoordinatorAgentService(
                        rag_service=self.rag_service,
                        router_service=self.router,
                        rag_anthropic_service=self.rag_anthropic_service,
                        rag_google_service=self.rag_google_service
                    )
                    logger.info("✓ Coordinator agent enabled")
                except Exception as e:
                    logger.error(f"Failed to initialize coordinator agent: {e}")
                    logger.warning("Continuing without coordinator agent")
        else:
            logger.info("✗ Coordinator agent disabled")

        logger.info("🚀 RAG Agent Application initialized successfully")

    async def create_session(self, user_id: str = "local_user") -> str:
        """
        Create a new chat session.

        Args:
            user_id: User identifier

        Returns:
            Session ID
        """
        return await self.adk_agent.create_session(user_id)

    async def create_coordinator_session(self, user_id: str = "local_user") -> str:
        """
        Create a new chat session for coordinator agent.

        Args:
            user_id: User identifier

        Returns:
            Session ID
        """
        if self.coordinator_agent:
            return await self.coordinator_agent.create_session(user_id)
        else:
            return await self.create_session(user_id)

    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> str:
        """
        Process a chat message with optional routing.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Response string (backwards compatible)
        """
        self._last_routing = None
        if self.router and self.router.enabled:
            try:
                self._last_routing = self.router.route(message)
                logger.info(
                    f"🎯 Routed to '{self._last_routing['primary_agent']}' "
                    f"(confidence: {self._last_routing['confidence']:.2f})"
                )
            except Exception as e:
                logger.error(f"Routing failed, continuing without routing: {e}")
                self._last_routing = None

        response = await self.adk_agent.chat(
            message=message,
            user_id=user_id,
            session_id=session_id
        )

        return response

    async def coordinator_chat(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> str:
        """
        Process a chat message using coordinator with specialist delegation.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Response string (matches existing chat format)
        """
        if not self.coordinator_agent:
            logger.warning("Coordinator agent not available, falling back to regular chat")
            return await self.chat(message, user_id, session_id)

        logger.info(f"Processing coordinator chat for session {session_id}")

        response = await self.coordinator_agent.chat(
            message=message,
            user_id=user_id,
            session_id=session_id
        )

        return response

    async def coordinator_chat_stream(
            self,
            message: str,
            user_id: str,
            session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a chat message using coordinator with streaming response.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Yields:
            Event dictionaries with routing info and response chunks
        """
        if not self.coordinator_agent:
            logger.warning("Coordinator agent not available for streaming")
            yield {
                "type": "error",
                "data": {"message": "Coordinator agent not available"}
            }
            return

        logger.info(f"Processing streaming coordinator chat for session {session_id}")

        async for event in self.coordinator_agent.chat_stream(
                message=message,
                user_id=user_id,
                session_id=session_id
        ):
            yield event

    def get_last_routing(self) -> Optional[Dict[str, Any]]:
        """
        Get routing info from the last chat call.

        Returns:
            Routing decision dict or None
        """
        return getattr(self, '_last_routing', None)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get application statistics.

        Returns:
            Stats dictionary
        """
        doc_count = 0
        if self.vector_store:
            try:
                collection = self.vector_store.get_collection()
                doc_count = collection.count()
            except Exception:
                pass

        stats = {
            "provider_type": settings.provider_type,
            "vector_store_collection": settings.collection_name if self.vector_store else None,
            "document_count": doc_count,
            "router_enabled": self.router.enabled if self.router else False,
            "coordinator_enabled": self.coordinator_agent is not None,
            "services": {
                "local_rag": self.rag_service is not None,
                "anthropic": self.rag_anthropic_service is not None,
                "google": self.rag_google_service is not None
            }
        }

        if settings.provider_type == "ollama":
            stats["embedding_model"] = settings.embedding_model
            stats["chat_model"] = settings.chat_model
        elif settings.provider_type == "llamacpp":
            stats["chat_model"] = settings.llamacpp_chat_model_path

        if self.router and self.router.enabled:
            stats["router_model"] = settings.router_model_path

        if self.coordinator_agent:
            specialist_status = self.coordinator_agent.get_specialist_status()
            stats["coordinator_specialists"] = {
                "anthropic": specialist_status["anthropic"]["available"],
                "google": specialist_status["google"]["available"],
                "local": specialist_status["local"]["available"]
            }

        return stats