"""
Google ADK Agent service.
"""
import uuid
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from config import settings, logger
from app.services.rag import RAGService


class ADKAgentService:
    """Service for managing Google ADK agent interactions."""
    
    def __init__(self, rag_service: RAGService):
        """
        Initialize ADK agent service.
        
        Args:
            rag_service: RAGService instance
        """
        self.rag_service = rag_service
        self.session_service = InMemorySessionService()
        self.agent = self._create_agent()
        self.runner = Runner(
            agent=self.agent,
            app_name=settings.app_name,
            session_service=self.session_service
        )
        logger.info(f"ADK Agent initialized with model: {settings.chat_model}")
    
    def _create_agent(self) -> LlmAgent:
        """Create and configure the ADK agent."""
        local_llm = LiteLlm(model=f"ollama_chat/{settings.chat_model}")
        
        agent = LlmAgent(
            name="rag_assistant",
            model=local_llm,
            tools=[self._rag_query_tool],
            output_key="rag_result",
            instruction=(
                "You are a helpful and knowledgeable RAG assistant. "
                "When the user asks a question, ALWAYS call the rag_query() tool "
                "to retrieve information from the knowledge base. "
                "Provide accurate, helpful answers based on the retrieved information."
            )
        )
        
        return agent
    
    def _rag_query_tool(self, query: str) -> str:
        """
        Tool function for RAG queries.
        
        Args:
            query: User's question
        
        Returns:
            Answer with citations
        """
        logger.debug(f"[Tool] rag_query called: '{query}'")
        answer, _ = self.rag_service.query(query)
        return answer
    
    async def create_session(self, user_id: str = "local_user") -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: User identifier
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        await self.session_service.create_session(
            app_name=settings.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        logger.info(f"Created session: {session_id}")
        return session_id
    
    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> str:
        """
        Send a message and get a response.
        
        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier
        
        Returns:
            Assistant's response
        """
        logger.info(f"Processing message in session {session_id}")
        
        content = types.Content(
            role='user',
            parts=[types.Part(text=message)]
        )
        
        response_text = ""
        
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response() and event.content:
                response_text = event.content.parts[0].text.strip()
        
        return response_text
