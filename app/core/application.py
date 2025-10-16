"""
Core application class that orchestrates all services.
"""
import os
from pathlib import Path
from typing import Optional, Tuple, List

from config import settings, logger
from app.services.vector_store import VectorStoreService
from app.services.rag import RAGService
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService
from app.services.adk_agent import ADKAgentService


class RAGAgentApp:
    """Main application class with multi-provider support."""

    def __init__(self):
        """Initialize the application and all services."""
        logger.info(f"Initializing {settings.app_name} v{settings.version}")

        # Initialize services in dependency order
        self.vector_store = VectorStoreService()
        self.rag_service = RAGService(self.vector_store)

        # Initialize provider-specific services if API keys are available
        self.rag_anthropic_service = None
        self.rag_google_service = None

        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.rag_anthropic_service = RAGAnthropicService(self.vector_store)
                logger.info("✅ Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"⚠️  Anthropic provider not available: {e}")

        if os.getenv("GOOGLE_API_KEY"):
            try:
                self.rag_google_service = RAGGoogleService(self.vector_store)
                logger.info("✅ Google provider initialized")
            except Exception as e:
                logger.warning(f"⚠️  Google provider not available: {e}")

        # Initialize ADK agent with all available providers
        self.adk_agent = ADKAgentService(
            self.rag_service,
            self.rag_anthropic_service,
            self.rag_google_service
        )

        logger.info("✅ Application initialized successfully")

    def ingest_documents(
        self,
        directory: Optional[Path] = None,
        file_types: Optional[List[str]] = None,
        overwrite: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Ingest documents (PDF, CSV, JSONL) into the knowledge base.

        Args:
            directory: Directory containing documents
            file_types: List of file types to ingest ['pdf', 'csv', 'jsonl']
            overwrite: Whether to overwrite existing collection

        Returns:
            Tuple of (num_documents, num_chunks, filenames)
        """
        return self.vector_store.ingest_documents(directory, file_types, overwrite)

    def get_stats(self) -> dict:
        """Get application statistics."""
        vector_stats = self.vector_store.get_stats()

        providers = {
            "local": True,
            "anthropic": self.rag_anthropic_service is not None,
            "google": self.rag_google_service is not None
        }

        return {
            "app_name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "vector_store": vector_stats,
            "models": {
                "embedding": settings.embedding_model,
                "chat": settings.chat_model
            },
            "providers": providers
        }

    async def create_session(self, user_id: str = "local_user") -> str:
        """Create a new chat session."""
        return await self.adk_agent.create_session(user_id)

    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> str:
        """
        Send a chat message.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Assistant's response
        """
        return await self.adk_agent.chat(message, user_id, session_id)

    def query_rag(
        self,
        question: str,
        k: Optional[int] = None,
        provider: str = "local"
    ) -> Tuple[str, Optional[List[str]]]:
        """
        Query the RAG system directly (without agent).

        Args:
            question: User's question
            k: Number of documents to retrieve
            provider: Provider to use ('local', 'anthropic', 'google')

        Returns:
            Tuple of (answer, sources)
        """
        if provider == "anthropic" and self.rag_anthropic_service:
            return self.rag_anthropic_service.query(question, k)
        elif provider == "google" and self.rag_google_service:
            return self.rag_google_service.query(question, k)
        else:
            return self.rag_service.query(question, k)