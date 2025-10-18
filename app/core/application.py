"""
Main application class integrating all services with optional routing and coordination.
"""
from typing import Optional, Dict, Any

from config import settings, logger
from app.services.vector_store import VectorStoreService
from app.services.rag import RAGService
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService
from app.services.adk_agent import ADKAgentService
from app.services.coordinator_agent import CoordinatorAgentService
from app.services.router import RouterService


class RAGAgentApp:
    """Main application integrating vector store, RAG, and agent services."""

    def __init__(self):
        """Initialize application with all services."""
        logger.info("Initializing RAG Agent Application")

        # Initialize vector store
        self.vector_store = VectorStoreService()

        # Initialize RAG services
        self.rag_service = RAGService(self.vector_store)

        # Initialize optional provider services
        self.rag_anthropic_service = None
        self.rag_google_service = None

        # Check for Anthropic configuration
        try:
            import os
            if os.getenv("ANTHROPIC_API_KEY"):
                self.rag_anthropic_service = RAGAnthropicService(self.vector_store)
                logger.info("Anthropic RAG service enabled")
        except Exception as e:
            logger.warning(f"Anthropic RAG service not available: {e}")

        # Check for Google configuration
        try:
            import os
            if os.getenv("GOOGLE_API_KEY"):
                self.rag_google_service = RAGGoogleService(self.vector_store)
                logger.info("Google RAG service enabled")
        except Exception as e:
            logger.warning(f"Google RAG service not available: {e}")

        # Initialize ADK agent (existing single-agent behavior)
        self.adk_agent = ADKAgentService(
            rag_service=self.rag_service,
            rag_anthropic_service=self.rag_anthropic_service,
            rag_google_service=self.rag_google_service
        )

        # Initialize coordinator agent (optional, NEW)
        self.coordinator_agent = None
        if settings.use_coordinator_agent:
            try:
                self.coordinator_agent = CoordinatorAgentService(
                    rag_service=self.rag_service,
                    rag_anthropic_service=self.rag_anthropic_service,
                    rag_google_service=self.rag_google_service
                )
                logger.info("✓ Coordinator agent enabled with specialist delegation")
            except Exception as e:
                logger.error(f"Failed to initialize coordinator agent: {e}")
                logger.warning("Continuing without coordinator agent")
        else:
            logger.info("✗ Coordinator agent disabled")

        # Initialize router (conditional on config)
        self.router = RouterService()

        if self.router.enabled:
            logger.info("✓ Router service enabled - requests will be analyzed before processing")
        else:
            logger.info("✗ Router service disabled - requests go directly to agent")

        logger.info("RAG Agent Application initialized successfully")

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
            # Fallback to regular session
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
        # Step 1: Route the request (if router is enabled)
        self._last_routing = None
        if self.router.enabled:
            try:
                self._last_routing = self.router.route(message)
                logger.info(
                    f"🎯 Routed to '{self._last_routing['primary_agent']}' "
                    f"(confidence: {self._last_routing['confidence']:.2f})"
                )
            except Exception as e:
                logger.error(f"Routing failed, continuing without routing: {e}")
                self._last_routing = None

        # Step 2: Process with agent
        # Note: Current agent handles all request types
        # In future iterations, we'll route to specialized agents based on routing_decision
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

        # Optional: Still use router for analytics even with coordinator
        self._last_routing = None
        if self.router.enabled:
            try:
                self._last_routing = self.router.route(message)
                logger.info(
                    f"🎯 Router classified as '{self._last_routing['primary_agent']}' "
                    f"(confidence: {self._last_routing['confidence']:.2f})"
                )
            except Exception as e:
                logger.debug(f"Router classification failed: {e}")

        # Use coordinator agent with automatic delegation
        response = await self.coordinator_agent.chat(
            message=message,
            user_id=user_id,
            session_id=session_id
        )

        return response

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
        # Get document count
        try:
            collection = self.vector_store.get_collection()
            doc_count = collection.count()
        except Exception:
            doc_count = 0

        stats = {
            "provider_type": settings.provider_type,
            "vector_store_collection": settings.collection_name,
            "document_count": doc_count,
            "router_enabled": self.router.enabled,
            "coordinator_enabled": self.coordinator_agent is not None
        }

        # Add model info based on provider
        if settings.provider_type == "ollama":
            stats["embedding_model"] = settings.embedding_model
            stats["chat_model"] = settings.chat_model
        elif settings.provider_type == "llamacpp":
            stats["chat_model"] = settings.llamacpp_chat_model_path

        # Add router info if enabled
        if self.router.enabled:
            stats["router_model"] = settings.router_model_path

        # Add coordinator info if enabled
        if self.coordinator_agent:
            stats["coordinator_specialists"] = len(self.coordinator_agent.specialist_agents)

        return stats