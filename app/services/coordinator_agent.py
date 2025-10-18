"""
Coordinator Agent service with specialist delegation using ADK.
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
from app.services.specialized_agents import SpecializedAgentsFactory


class CoordinatorAgentService:
    """Service for managing coordinator agent with specialist delegation."""

    def __init__(
        self,
        rag_service: RAGService,
        rag_anthropic_service: Optional[RAGAnthropicService] = None,
        rag_google_service: Optional[RAGGoogleService] = None
    ):
        """
        Initialize coordinator agent service.

        Args:
            rag_service: RAGService instance (required)
            rag_anthropic_service: Optional RAGAnthropicService instance
            rag_google_service: Optional RAGGoogleService instance
        """
        self.rag_service = rag_service
        self.rag_anthropic_service = rag_anthropic_service
        self.rag_google_service = rag_google_service
        self.session_service = InMemorySessionService()
        self.provider_type = settings.provider_type

        # Create specialized agents
        logger.info("Creating specialized agents via factory")
        self.factory = SpecializedAgentsFactory(
            rag_service=rag_service,
            rag_anthropic_service=rag_anthropic_service,
            rag_google_service=rag_google_service
        )
        self.specialist_agents = self.factory.create_all_agents()

        # Keep reference to general_assistant for fallback
        self.general_assistant = next(
            agent for agent in self.specialist_agents
            if agent.name == "general_assistant"
        )

        # Create coordinator agent
        self.coordinator = self._create_coordinator_agent()

        # Create runner
        self.runner = Runner(
            agent=self.coordinator,
            app_name=settings.app_name,
            session_service=self.session_service
        )

        logger.info(
            f"CoordinatorAgentService initialized with {len(self.specialist_agents)} specialists"
        )

    def _create_coordinator_model(self) -> LiteLlm:
        """Create model for coordinator agent."""
        if settings.provider_type == "ollama":
            return LiteLlm(
                model="ollama_chat/phi3:mini",  # Fast model for routing
                supports_function_calling=True
            )
        else:  # llamacpp
            return LiteLlm(
                model="openai/local-model",
                api_base=f"http://{settings.llama_server_host}:{settings.llama_server_port}/v1",
                api_key="dummy",
                supports_function_calling=True
            )

    def _create_coordinator_agent(self) -> LlmAgent:
        """Create coordinator agent with specialist sub-agents."""
        coordinator_model = self._create_coordinator_model()

        # Build specialist descriptions for instruction
        specialist_list = "\n".join([
            f"- {agent.name}: {agent.description}"
            for agent in self.specialist_agents
        ])

        coordinator = LlmAgent(
            name="coordinator",
            model=coordinator_model,
            description="Routes user requests to appropriate specialist agents",
            instruction=f"""You are a helpful coordinator assistant. Your job is to analyze the user's request and delegate it to the most appropriate specialist agent.

Available specialists:
{specialist_list}

To delegate a request, use: transfer_to_agent(agent_name='specialist_name')

Choose the specialist that best matches the user's needs based on their descriptions. If you're unsure or the request is simple casual conversation, use 'general_assistant'.""",
            sub_agents=self.specialist_agents
        )

        logger.info(f"Coordinator agent created with {len(self.specialist_agents)} sub-agents")
        return coordinator

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

        logger.info(f"Created coordinator session: {session_id}")
        return session_id

    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> str:
        """
        Send a message and get a response via coordinator delegation.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Assistant's response string
        """
        logger.info(f"Processing coordinator chat for session {session_id}")

        try:
            # Use coordinator with automatic delegation
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

                # Check if this is the final response
                if event.is_final_response():
                    logger.info(f"Found final response in event #{event_count}")
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                        logger.info(f"Final response from: {event.author}")
                        break

            logger.info(f"Total events processed: {event_count}")

            if final_response is None:
                logger.error("No final response from coordinator, falling back to general assistant")
                return await self._fallback_to_general_assistant(message, user_id, session_id)

            return final_response

        except Exception as e:
            logger.error(f"Error in coordinator chat: {e}", exc_info=True)
            logger.info("Falling back to general assistant due to error")
            return await self._fallback_to_general_assistant(message, user_id, session_id)

    async def _fallback_to_general_assistant(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> str:
        """
        Fallback to general assistant if coordinator fails.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            General assistant's response
        """
        logger.warning("Using fallback: general_assistant")

        try:
            # Create a temporary runner for just the general assistant
            fallback_runner = Runner(
                agent=self.general_assistant,
                app_name=settings.app_name,
                session_service=self.session_service
            )

            result_generator = fallback_runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=message)]
                )
            )

            async for event in result_generator:
                if event.is_final_response():
                    if event.content and event.content.parts:
                        return event.content.parts[0].text

            # If still no response, return default message
            return "I apologize, but I'm having trouble processing your request. Please try again."

        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
            return "I apologize, but I'm having trouble processing your request. Please try again."