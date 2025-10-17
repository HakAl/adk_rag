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
            "You are a helpful assistant. When the user asks a question:\n"
            "1. If it's about code, debugging, or general knowledge, answer directly using your knowledge\n"
            "2. If it requires information from documents in the knowledge base, use the appropriate RAG tool\n\n"
            "Available RAG tools:\n"
            "- rag_query(): Use for queries that need information from the knowledge base (fast, local)\n"
        )

        if self.rag_anthropic_service:
            instruction += (
                "- rag_query_anthropic(): Use when you need the knowledge base AND complex reasoning\n"
            )

        if self.rag_google_service:
            instruction += (
                "- rag_query_google(): Use when you need the knowledge base for factual queries\n"
            )

        instruction += (
            "\nIMPORTANT: Only use RAG tools when the answer requires information from the knowledge base. "
            "For general questions, code review, or common knowledge, answer directly without using tools.\n"
            "Always provide a clear, helpful response to the user."
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

        # Runner.run() returns a generator that yields events
        result_generator = self.runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
        )

        # Iterate through events and collect responses
        final_response = None
        for event in result_generator:
            # Log event details for debugging
            logger.debug(f"Event type: {type(event).__name__}")

            # Try to extract response from various event attributes
            # Option 1: Check for output_key in state
            if hasattr(event, 'state') and hasattr(event.state, self.agent.output_key):
                response = getattr(event.state, self.agent.output_key)
                if response:
                    final_response = response
                    logger.debug(f"Found response in state.{self.agent.output_key}")

            # Option 2: Direct output_key attribute
            elif hasattr(event, self.agent.output_key):
                response = getattr(event, self.agent.output_key)
                if response:
                    final_response = response
                    logger.debug(f"Found response in {self.agent.output_key}")

            # Option 3: Check content
            elif hasattr(event, 'content'):
                if isinstance(event.content, str):
                    final_response = event.content
                    logger.debug("Found response in content (string)")
                elif hasattr(event.content, 'parts') and event.content.parts:
                    final_response = event.content.parts[0].text
                    logger.debug("Found response in content.parts")

        if final_response is None:
            logger.error("No response found in any event")
            return "I apologize, but I couldn't generate a proper response. Please try again."

        # Clean up the response if it contains tool metadata
        response_str = str(final_response)

        # If response looks like raw tool calls/JSON, that's an error
        if response_str.strip().startswith('{"name":') or '"parameters"' in response_str:
            logger.warning(f"Agent returned tool metadata instead of answer: {response_str[:200]}")
            return "I apologize, but I had trouble processing that request. Please try rephrasing your question."

        return response_str