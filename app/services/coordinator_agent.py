"""
Coordinator Agent service with specialist delegation using router-based classification.
"""
import uuid
from typing import Optional, Dict, Any

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
from app.services.router import RouterService


class CoordinatorAgentService:
    """Service for managing coordinator agent with router-based specialist delegation."""

    def __init__(
        self,
        rag_service: RAGService,
        router_service: RouterService,
        rag_anthropic_service: Optional[RAGAnthropicService] = None,
        rag_google_service: Optional[RAGGoogleService] = None
    ):
        """
        Initialize coordinator agent service.

        Args:
            rag_service: RAGService instance (required)
            router_service: RouterService instance (required)
            rag_anthropic_service: Optional RAGAnthropicService instance
            rag_google_service: Optional RAGGoogleService instance
        """
        self.rag_service = rag_service
        self.router_service = router_service
        self.rag_anthropic_service = rag_anthropic_service
        self.rag_google_service = rag_google_service
        self.session_service = InMemorySessionService()
        self.provider_type = settings.provider_type

        logger.info("Creating specialized agents via factory")
        self.factory = SpecializedAgentsFactory(
            rag_service=rag_service,
            rag_anthropic_service=rag_anthropic_service,
            rag_google_service=rag_google_service
        )
        self.specialist_agents = self.factory.create_all_agents()

        self.specialists_by_type = self._map_specialists()

        self.general_assistant = next(
            agent for agent in self.specialist_agents
            if agent.name == "general_assistant"
        )

        self.runners = self._create_specialist_runners()

        logger.info(
            f"CoordinatorAgentService initialized with {len(self.specialist_agents)} specialists "
            f"and router-based delegation"
        )

    def _map_specialists(self) -> Dict[str, LlmAgent]:
        """
        Map router classifications to specialist agents.

        Returns:
            Dict mapping router agent types to specialist agents
        """
        mapping = {}

        for agent in self.specialist_agents:
            if agent.name == "code_validator":
                mapping["code_validation"] = agent
            elif agent.name == "rag_specialist":
                mapping["rag_query"] = agent
            elif agent.name == "code_generator":
                mapping["code_generation"] = agent
            elif agent.name == "code_analyzer":
                mapping["code_analysis"] = agent
            elif agent.name == "reasoning_specialist":
                mapping["complex_reasoning"] = agent
            elif agent.name == "general_assistant":
                mapping["general_chat"] = agent

        logger.info(f"Mapped {len(mapping)} specialist types")
        return mapping

    def _create_specialist_runners(self) -> Dict[str, Runner]:
        """
        Create individual runners for each specialist.

        Returns:
            Dict mapping agent names to runners
        """
        runners = {}
        for agent in self.specialist_agents:
            runners[agent.name] = Runner(
                agent=agent,
                app_name=settings.app_name,
                session_service=self.session_service
            )
        return runners

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
        Send a message and get a response via router-based specialist delegation.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Assistant's response string
        """
        logger.info(f"Processing coordinator chat for session {session_id}")

        try:
            routing_decision = self.router_service.route(message)

            agent_type = routing_decision["primary_agent"]
            confidence = routing_decision["confidence"]

            logger.info(
                f"Router classified as '{agent_type}' "
                f"(confidence: {confidence:.2f})"
            )

            specialist = self.specialists_by_type.get(agent_type)

            if specialist is None:
                logger.warning(f"No specialist found for type '{agent_type}', using general_assistant")
                specialist = self.general_assistant

            runner = self.runners[specialist.name]

            logger.info(f"Delegating to specialist: {specialist.name}")

            result_generator = runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=message)]
                )
            )

            final_response = None
            event_count = 0

            async for event in result_generator:
                event_count += 1
                logger.debug(f"Event #{event_count}: {type(event).__name__}")

                if event.is_final_response():
                    logger.info(f"Found final response in event #{event_count}")
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                        logger.info(f"Final response from: {event.author}")
                        break

            logger.info(f"Total events processed: {event_count}")

            if final_response is None:
                logger.error("No final response from specialist, falling back to general assistant")
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
        Fallback to general assistant if routing or specialist fails.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            General assistant's response
        """
        logger.warning("Using fallback: general_assistant")

        try:
            fallback_runner = self.runners[self.general_assistant.name]

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

            return "I apologize, but I'm having trouble processing your request. Please try again."

        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
            return "I apologize, but I'm having trouble processing your request. Please try again."