"""
Google ADK Agent service with multi-provider tool support.
"""
import uuid
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.genai import types

from config import settings, logger
from app.services.rag import RAGService
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService
from app.tools import validate_code, create_rag_tools
from app.db.session_service import PostgreSQLSessionService


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
        self.session_service = PostgreSQLSessionService()
        self.provider_type = settings.provider_type
        self.agent = self._create_agent()

        # Create runner
        self.runner = Runner(
            agent=self.agent,
            app_name=settings.app_name,
            session_service=self.session_service
        )

        providers = [settings.provider_type]
        if rag_anthropic_service:
            providers.append("anthropic")
        if rag_google_service:
            providers.append("google")

        logger.info(f"ADK Agent initialized with providers: {', '.join(providers)}")

        if settings.provider_type == 'llamacpp':
            logger.warning(
                "⚠️  llama.cpp detected. ADK tool calling requires one of:\n"
                "   1. Run llama-server: ./llama-server -m model.gguf --port 8080\n"
                "   2. Switch to Ollama for better tool support\n"
                "   3. Tools will be disabled if llama-server is not running"
            )

    def _create_agent(self) -> LlmAgent:
        """Create and configure the ADK agent with all available tools."""

        # Configure model based on provider type
        if settings.provider_type == 'llamacpp':
            local_llm, tools_enabled = self._configure_llamacpp()
        elif settings.provider_type == 'ollama':
            local_llm, tools_enabled = self._configure_ollama()
        else:
            raise ValueError(f"Unsupported provider for ADK: {settings.provider_type}")

        # Build tools and instructions
        if tools_enabled:
            tools = self._build_tools()
            instruction = self._build_instruction_with_tools()
        else:
            tools = []
            instruction = self._build_instruction_without_tools()
            logger.warning("Tools disabled - agent will function as a basic chat assistant")

        agent = LlmAgent(
            name="rag_assistant",
            model=local_llm,
            tools=tools,
            output_key="rag_result",
            instruction=instruction
        )

        return agent

    def _configure_llamacpp(self) -> tuple[LiteLlm, bool]:
        """
        Configure llama.cpp provider.

        Returns:
            Tuple of (LiteLlm instance, tools_enabled)
        """
        logger.info("Configuring ADK for llama.cpp via llama-server")

        # Check if llama-server is running
        try:
            import requests
            llama_server_url = f"http://{settings.llama_server_host}:{settings.llama_server_port}"
            response = requests.get(f"{llama_server_url}/health", timeout=2)
            if response.status_code == 200:
                logger.info("✓ llama-server detected, tool calling enabled")
                tools_enabled = True
            else:
                logger.warning("✗ llama-server not responding, tools disabled")
                tools_enabled = False
        except Exception:
            logger.warning(
                f"✗ llama-server not running at {settings.llama_server_host}:{settings.llama_server_port}, tools disabled")
            tools_enabled = False

        local_llm = LiteLlm(
            model="openai/local-model",
            api_base=f"http://{settings.llama_server_host}:{settings.llama_server_port}/v1",
            api_key="dummy",
            supports_function_calling=tools_enabled
        )

        return local_llm, tools_enabled

    def _configure_ollama(self) -> tuple[LiteLlm, bool]:
        """
        Configure Ollama provider.

        Returns:
            Tuple of (LiteLlm instance, tools_enabled)
        """
        logger.info(f"Configuring ADK for Ollama with model: {settings.chat_model}")
        local_llm = LiteLlm(
            model=f"ollama_chat/{settings.chat_model}",
            supports_function_calling=True
        )
        return local_llm, True

    def _build_tools(self) -> list:
        """
        Build list of available tools.

        Returns:
            List of tool functions
        """
        # Start with validation tool
        tools = [validate_code]

        # Add RAG tools
        rag_tools = create_rag_tools(
            rag_service=self.rag_service,
            rag_anthropic_service=self.rag_anthropic_service,
            rag_google_service=self.rag_google_service
        )
        tools.extend(rag_tools)

        return tools

    def _build_instruction_with_tools(self) -> str:
        """Build instruction text when tools are enabled."""
        instruction_parts = [
            "You are a helpful assistant. When the user asks a question:\n"
            "1. If it's about code validation or syntax checking, use the validate_code tool\n"
            "2. If it requires information from documents in the knowledge base, use the appropriate RAG tool\n"
            "3. For general questions or explanations, answer directly using your knowledge\n\n"
            "Available tools:\n"
            "- validate_code(code, language): Validate code syntax (supports python, javascript, json)\n"
            "- rag_query(query): Use for queries that need information from the knowledge base (fast, local)"
        ]

        if self.rag_anthropic_service:
            instruction_parts.append(
                "\n- rag_query_anthropic(query): Use when you need the knowledge base AND complex reasoning"
            )

        if self.rag_google_service:
            instruction_parts.append(
                "\n- rag_query_google(query): Use when you need the knowledge base for factual queries"
            )

        instruction_parts.append(
            "\n\nIMPORTANT: Only use these specific tools when needed. "
            "For general questions, code explanations, or common knowledge, answer directly without using tools.\n"
            "Always provide a clear, helpful response to the user."
        )

        return "".join(instruction_parts)

    def _build_instruction_without_tools(self) -> str:
        """Build instruction text when tools are disabled."""
        return (
            "You are a helpful assistant. Answer questions directly using your knowledge. "
            "Provide clear, concise, and accurate responses to the best of your ability."
        )

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
            session_id=session_id,
            agent_type="adk"
        )

        logger.info(f"Created ADK session: {session_id}")
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

        # FIXED: Ensure session exists before processing
        await self._ensure_session_exists(session_id, user_id)

        # Use async generator
        result_generator = self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
        )

        # Collect events and look for final response
        final_response = None
        event_count = 0

        async for event in result_generator:
            event_count += 1
            logger.debug(f"Event #{event_count}: {type(event).__name__}")

            # Check if this is the final response using the official method
            if event.is_final_response():
                logger.info(f"Found final response in event #{event_count}")
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                    logger.info(f"Final response text: {final_response[:100]}")
                    break

        logger.info(f"Total events processed: {event_count}")

        if final_response is None:
            logger.error("No final response found")
            return "I apologize, but I couldn't generate a proper response. Please try again."

        return final_response

    async def _ensure_session_exists(self, session_id: str, user_id: str) -> None:
        """
        Ensure session exists in database, create if missing.

        Args:
            session_id: Session identifier
            user_id: User identifier
        """
        exists = await self.session_service.session_exists(session_id)
        if not exists:
            logger.warning(
                f"Session {session_id} not found in database, auto-creating"
            )
            await self.session_service.create_session(
                app_name=settings.app_name,
                user_id=user_id,
                session_id=session_id,
                agent_type="adk"
            )