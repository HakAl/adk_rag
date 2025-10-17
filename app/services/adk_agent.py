"""
Google ADK Agent service with multi-provider tool support.
"""
import uuid
import ast
import subprocess
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


# Define standalone tool functions (not methods)
def validate_code(code: str, language: str) -> str:
    """
    Validate code syntax for various programming languages.

    Args:
        code: Code to validate
        language: Programming language (python, javascript, json)

    Returns:
        Validation result with details
    """
    # Default to python if language is empty
    if not language or not language.strip():
        language = "python"

    language = language.lower().strip()
    logger.debug(f"[Tool] validate_code called for {language}")

    try:
        if language == "python":
            return _validate_python(code)
        elif language in ["javascript", "js"]:
            return _validate_javascript(code)
        elif language == "json":
            return _validate_json(code)
        else:
            return f"⚠️ Language '{language}' not supported. Supported: python, javascript, json"
    except Exception as e:
        logger.error(f"Code validation error: {e}")
        return f"❌ Validation error: {str(e)}"


def _validate_python(code: str) -> str:
    """Validate Python code syntax."""
    try:
        ast.parse(code)
        return "✅ Python code syntax is valid."
    except SyntaxError as e:
        return f"❌ Python syntax error on line {e.lineno}: {e.msg}\n  {e.text or ''}"
    except Exception as e:
        return f"❌ Python validation error: {str(e)}"


def _validate_javascript(code: str) -> str:
    """Validate JavaScript code syntax using Node.js if available."""
    try:
        result = subprocess.run(
            ['node', '--check', '-'],
            input=code,
            text=True,
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0:
            return "✅ JavaScript code syntax is valid."
        else:
            return f"❌ JavaScript syntax error:\n{result.stderr}"

    except FileNotFoundError:
        if code.strip():
            return "⚠️ JavaScript validation requires Node.js (not installed). Basic check: code is non-empty."
        return "❌ JavaScript code is empty."
    except subprocess.TimeoutExpired:
        return "❌ JavaScript validation timed out."
    except Exception as e:
        return f"❌ JavaScript validation error: {str(e)}"


def _validate_json(code: str) -> str:
    """Validate JSON syntax."""
    import json
    try:
        json.loads(code)
        return "✅ JSON syntax is valid."
    except json.JSONDecodeError as e:
        return f"❌ JSON syntax error at line {e.lineno}, column {e.colno}: {e.msg}"
    except Exception as e:
        return f"❌ JSON validation error: {str(e)}"


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
            # For llama.cpp, try to connect to llama-server (OpenAI-compatible API)
            # User must run: ./llama-server -m model.gguf --port 8080
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
                api_key="dummy",  # llama-server doesn't need auth, but LiteLLM requires this field
                supports_function_calling=tools_enabled
            )

        elif settings.provider_type == 'ollama':
            # For Ollama, use ollama_chat which has native tool calling
            logger.info(f"Configuring ADK for Ollama with model: {settings.chat_model}")
            local_llm = LiteLlm(
                model=f"ollama_chat/{settings.chat_model}",
                supports_function_calling=True
            )
            tools_enabled = True

        else:
            raise ValueError(f"Unsupported provider for ADK: {settings.provider_type}")

        # Build list of available tools if enabled
        if tools_enabled:
            tools = [
                self._create_rag_query_tool(),
                validate_code
            ]

            if self.rag_anthropic_service:
                tools.append(self._create_rag_anthropic_tool())

            if self.rag_google_service:
                tools.append(self._create_rag_google_tool())

            # Build instruction with tool descriptions
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
        else:
            # No tools available - simple chat agent
            tools = []
            instruction_parts = [
                "You are a helpful assistant. Answer questions directly using your knowledge. "
                "Provide clear, concise, and accurate responses to the best of your ability."
            ]
            logger.warning("Tools disabled - agent will function as a basic chat assistant")

        instruction = "".join(instruction_parts)

        agent = LlmAgent(
            name="rag_assistant",
            model=local_llm,
            tools=tools,
            output_key="rag_result",
            instruction=instruction
        )

        return agent

    def _create_rag_query_tool(self):
        """Create RAG query tool as a closure."""
        rag_service = self.rag_service

        def rag_query(query: str) -> str:
            """
            Query the local knowledge base using RAG.

            Args:
                query: User's question

            Returns:
                Answer with citations
            """
            logger.debug(f"[Tool] rag_query (local) called: '{query}'")
            answer, _ = rag_service.query(query)
            return answer

        return rag_query

    def _create_rag_anthropic_tool(self):
        """Create Anthropic RAG query tool as a closure."""
        rag_anthropic_service = self.rag_anthropic_service

        def rag_query_anthropic(query: str) -> str:
            """
            Query the knowledge base using Anthropic Claude for complex reasoning.

            Args:
                query: User's question

            Returns:
                Answer with citations
            """
            logger.debug(f"[Tool] rag_query_anthropic called: '{query}'")
            answer, _ = rag_anthropic_service.query(query)
            return answer

        return rag_query_anthropic

    def _create_rag_google_tool(self):
        """Create Google RAG query tool as a closure."""
        rag_google_service = self.rag_google_service

        def rag_query_google(query: str) -> str:
            """
            Query the knowledge base using Google Gemini.

            Args:
                query: User's question

            Returns:
                Answer with citations
            """
            logger.debug(f"[Tool] rag_query_google called: '{query}'")
            answer, _ = rag_google_service.query(query)
            return answer

        return rag_query_google

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