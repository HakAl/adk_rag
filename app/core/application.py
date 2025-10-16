"""
Core application class that orchestrates all services.
"""
from pathlib import Path
from typing import Optional, Tuple, List

from config import settings, logger
from app.services.vector_store import VectorStoreService
from app.services.rag import RAGService
from app.services.adk_agent import ADKAgentService


class RAGAgentApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application and all services."""
        logger.info(f"Initializing {settings.app_name} v{settings.version}")
        
        # Initialize services in dependency order
        self.vector_store = VectorStoreService()
        self.rag_service = RAGService(self.vector_store)
        self.adk_agent = ADKAgentService(self.rag_service)
        
        logger.info("✅ Application initialized successfully")
    
    def ingest_documents(
        self,
        pdf_directory: Optional[Path] = None,
        overwrite: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Ingest PDF documents into the knowledge base.
        
        Args:
            pdf_directory: Directory containing PDFs
            overwrite: Whether to overwrite existing collection
        
        Returns:
            Tuple of (num_documents, num_chunks, filenames)
        """
        return self.vector_store.ingest_pdfs(pdf_directory, overwrite)
    
    def get_stats(self) -> dict:
        """Get application statistics."""
        vector_stats = self.vector_store.get_stats()
        
        return {
            "app_name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "vector_store": vector_stats,
            "models": {
                "embedding": settings.embedding_model,
                "chat": settings.chat_model
            }
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
        k: Optional[int] = None
    ) -> Tuple[str, Optional[List[str]]]:
        """
        Query the RAG system directly (without agent).
        
        Args:
            question: User's question
            k: Number of documents to retrieve
        
        Returns:
            Tuple of (answer, sources)
        """
        return self.rag_service.query(question, k)
