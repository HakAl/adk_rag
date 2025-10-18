"""
Coordinator Agent service with specialist delegation using router-based classification.
"""
import asyncio
import uuid
from typing import Optional, Dict, Any, List

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
        self.session_service = InMemorySessionService()  # SHARED session service
        self.provider_type = settings.provider_type

        logger.info("Creating specialized agents via factory")
        self.factory = SpecializedAgentsFactory(
            rag_service=rag_service,
            rag_anthropic_service=rag_anthropic_service,
            rag_google_service=rag_google_service
        )
        self.specialist_agents = self.factory.create_all_agents()

        # Direct category-to-agent mapping
        self.specialist_map = {
            "code_validation": self._get_agent("code_validator"),
            "rag_query": self._get_agent("rag_assistant"),
            "code_generation": self._get_agent("code_generator"),
            "code_analysis": self._get_agent("code_analyst"),
            "complex_reasoning": self._get_agent("complex_reasoner"),
            "general_chat": self._get_agent("general_assistant"),
        }

        # Category-keyed runners with SHARED session service
        self.specialist_runners = {}
        for category, agent in self.specialist_map.items():
            self.specialist_runners[category] = Runner(
                agent=agent,
                app_name=settings.app_name,
                session_service=self.session_service  # Shared for context continuity
            )

        # Human-readable names for specialists
        self.specialist_names = {
            "code_validation": "Code Validator",
            "rag_query": "Knowledge Base Assistant",
            "code_generation": "Code Generator",
            "code_analysis": "Code Analyst",
            "complex_reasoning": "Complex Reasoner",
            "general_chat": "General Assistant",
        }

        logger.info(
            f"CoordinatorAgentService initialized with {len(self.specialist_agents)} specialists "
            f"and router-based delegation"
        )

    def _get_agent(self, agent_name: str) -> LlmAgent:
        """
        Get agent by name from factory-created agents.

        Args:
            agent_name: Name of the agent to retrieve

        Returns:
            LlmAgent instance

        Raises:
            StopIteration: If agent not found
        """
        return next(
            agent for agent in self.specialist_agents
            if agent.name == agent_name
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

        Manual coordination with isolated specialist sessions and parallel execution support.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Assistant's response string
        """
        logger.info(f"Processing coordinator chat for session {session_id}")

        try:
            # Route to appropriate specialist(s)
            routing_decision = self.router_service.route(message)
            primary_agent = routing_decision["primary_agent"]
            parallel_agents = routing_decision.get("parallel_agents", [])
            confidence = routing_decision["confidence"]

            logger.info(
                f"Router classified as '{primary_agent}' "
                f"(confidence: {confidence:.2f}, parallel: {parallel_agents})"
            )

            # Check if parallel execution needed
            if parallel_agents:
                categories = [primary_agent] + parallel_agents
                responses = await self._run_parallel_specialists(
                    categories, message, user_id, session_id
                )
                return self._aggregate_responses(categories, responses)
            else:
                # Single specialist execution
                return await self._run_single_specialist(
                    primary_agent, message, user_id, session_id
                )

        except Exception as e:
            logger.error(f"Error in coordinator chat: {e}", exc_info=True)
            logger.info("Falling back to general assistant due to error")
            return await self._fallback_to_general_assistant(message, user_id, session_id)

    async def _run_single_specialist(
        self,
        agent_type: str,
        message: str,
        user_id: str,
        session_id: str
    ) -> str:
        """
        Run a single specialist and return its response.

        Args:
            agent_type: Specialist category
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Specialist's response string
        """
        # Get runner directly by category
        runner = self.specialist_runners.get(agent_type)

        if runner is None:
            logger.warning(f"No specialist found for type '{agent_type}', using general_chat")
            runner = self.specialist_runners["general_chat"]
            agent_type = "general_chat"

        logger.info(f"Delegating to specialist category: {agent_type}")

        # Run specialist in isolated session
        specialist_session_id = f"{session_id}-{agent_type}"

        result_generator = runner.run_async(
            user_id=user_id,
            session_id=specialist_session_id,  # Isolated session
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
        )

        # Collect final response
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

    async def _run_specialist(
        self,
        runner: Runner,
        message: str,
        user_id: str,
        specialist_session_id: str
    ) -> str:
        """
        Run a specialist and extract its response.

        Args:
            runner: Specialist runner
            message: User's message
            user_id: User identifier
            specialist_session_id: Isolated session ID

        Returns:
            Specialist's response string or empty string on failure
        """
        try:
            result_generator = runner.run_async(
                user_id=user_id,
                session_id=specialist_session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=message)]
                )
            )

            async for event in result_generator:
                if event.is_final_response():
                    if event.content and event.content.parts:
                        return event.content.parts[0].text

            return ""

        except Exception as e:
            logger.error(f"Specialist execution failed: {e}")
            return ""

    async def _run_parallel_specialists(
        self,
        categories: List[str],
        message: str,
        user_id: str,
        session_id: str
    ) -> List[str]:
        """
        Run multiple specialists concurrently.

        Args:
            categories: List of specialist categories
            message: User's message
            user_id: User identifier
            session_id: Base session identifier

        Returns:
            List of specialist responses (successful only)
        """
        logger.info(f"Running {len(categories)} specialists in parallel: {categories}")

        tasks = []
        for category in categories:
            runner = self.specialist_runners.get(category)
            if runner is None:
                logger.warning(f"Skipping unknown category: {category}")
                continue

            specialist_session_id = f"{session_id}-{category}"

            task = self._run_specialist(
                runner, message, user_id, specialist_session_id
            )
            tasks.append(task)

        # Run in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        successful_results = [
            r for r in results
            if isinstance(r, str) and r
        ]

        logger.info(f"Parallel execution completed: {len(successful_results)}/{len(tasks)} successful")

        return successful_results

    def _aggregate_responses(
        self,
        categories: List[str],
        responses: List[str]
    ) -> str:
        """
        Combine multiple specialist responses with labeled sections.

        Args:
            categories: List of specialist categories (in order)
            responses: List of specialist responses (in order)

        Returns:
            Aggregated response string
        """
        if len(responses) == 1:
            return responses[0]

        # Build aggregated response with specialist names
        aggregated = "Here are the results from multiple specialists:\n\n"

        for i, (category, response) in enumerate(zip(categories, responses)):
            specialist_name = self.specialist_names.get(category, category.replace("_", " ").title())
            aggregated += f"**{specialist_name}:**\n{response}\n\n"

        return aggregated.strip()

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
            fallback_runner = self.specialist_runners["general_chat"]

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