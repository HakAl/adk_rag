"""
Google ADK Agent service with multi-provider tool support.
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
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService


class ADKAgentService:
    """Service for managing Google ADK agent interactions with multi-provider tools."""

    def __init__(
        self,
        rag_service: RAGService,
        rag_anthropic_service: Optional[RAGAnthropicService] = None,
        rag_google_service: Optional[RAGGoogleService] = None
    ):
        """
        Initialize ADK agent service.

        Args:
            rag_service: RAGService instance (Ollama/local)
            rag_anthropic_service: Optional RAGAnthropicService instance
            rag_google_service: Optional RAGGoogleService instance
        """
        self.rag_service = rag_service
        self.rag_anthropic_service = rag_anthropic_service
        self.rag_google_service = rag_google_service
        self.session_service = InMemorySessionService()
        self.agent = self._create_agent()
        self.runner = Runner(
            agent=self.agent,
            app_name=settings.app_name,
            session_service=self.session_service
        )

        providers = ["local"]
        if rag_anthropic_service:
            providers.append("anthropic")
        if rag_google_service:
            providers.append("google")

        logger.info(f"ADK Agent initialized with providers: {', '.join(providers)}")

    def _create_agent(self) -> LlmAgent:
        """Create and configure the ADK agent with all available tools."""
        local_llm = LiteLlm(model=f"ollama_chat/{settings.chat_model}")

        # Build list of available tools
        tools = [self._rag_query_tool]

        if self.rag_anthropic_service:
            tools.append(self._rag_query_anthropic_tool)

        if self.rag_google_service:
            tools.append(self._rag_query_google_tool)

        # Enhanced instruction to help agent choose the right tool
        instruction = (
            "You are a helpful and knowledgeable RAG assistant with access to multiple AI providers. "
            "When the user asks a question, choose the most appropriate tool:\n"
            "- rag_query(): Use for general queries (fast, local processing)\n"
        )

        if self.rag_anthropic_service:
            instruction += (
                "- rag_query_anthropic(): Use for complex reasoning, analysis, or when high-quality "
                "responses are needed. Anthropic Claude excels at nuanced understanding.\n"
            )

        if self.rag_google_service:
            instruction += (
                "- rag_query_google(): Use for factual queries, summaries, or when you need "
                "fast responses. Google Gemini is excellent for information retrieval.\n"
            )

        instruction += (
            "\nConsider query characteristics:\n"
            "- Simple factual questions → rag_query() or rag_query_google()\n"
            "- Complex analysis/reasoning → rag_query_anthropic()\n"
            "- Technical deep-dives → rag_query_anthropic()\n"
            "- Quick summaries → rag_query_google() or rag_query()\n"
            "\nProvide accurate, helpful answers based on the retrieved information."
        )

        agent = LlmAgent(
            name="rag_assistant",
            model=local_llm,
            tools=tools,
            output_key="rag_result",
            instruction=instruction
        )

        return agent

    def _rag_query_tool(self, query: str) -> str:
        """
        Tool function for local RAG queries using Ollama.

        Args:
            query: User's question

        Returns:
            Answer with citations
        """
        logger.debug(f"[Tool] rag_query (local) called: '{query}'")
        answer, _ = self.rag_service.query(query)
        return answer

    def _rag_query_anthropic_tool(self, query: str) -> str:
        """
        Tool function for RAG queries using Anthropic Claude.

        Args:
            query: User's question

        Returns:
            Answer with citations
        """
        logger.debug(f"[Tool] rag_query_anthropic called: '{query}'")
        answer, _ = self.rag_anthropic_service.query(query)
        return answer

    def _rag_query_google_tool(self, query: str) -> str:
        """
        Tool function for RAG queries using Google Gemini.

        Args:
            query: User's question

        Returns:
            Answer with citations
        """
        logger.debug(f"[Tool] rag_query_google called: '{query}'")
        answer, _ = self.rag_google_service.query(query)
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
        logger.info(f"Processing chat message for session {session_id}")

        result = await self.runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
        )

        # Extract text from response
        if result and result.messages:
            last_message = result.messages[-1]
            if last_message.parts:
                return last_message.parts[0].text

        return "No response generated"