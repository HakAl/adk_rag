"""
Coordinator Agent service with cloud-first specialist delegation using router-based classification.
"""
import asyncio
import uuid
from typing import Optional, Dict, Any, List

from google.genai import types

from config import settings, logger
from app.services.rag import RAGService
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService
from app.services.router import RouterService
from app.services.specialist_manager import SpecialistManager


class CoordinatorAgentService:
    """Service for managing coordinator agent with cloud-first specialist delegation."""

    def __init__(
        self,
        rag_service: RAGService,
        router_service: RouterService,
        rag_anthropic_service: Optional[RAGAnthropicService] = None,
        rag_google_service: Optional[RAGGoogleService] = None
    ):
        """
        Initialize coordinator agent service with cloud specialists.

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

        # Use SpecialistManager for cloud-first specialists with fallback
        self.specialist_manager = SpecialistManager()

        # Session storage (simple in-memory for now)
        self.sessions: Dict[str, List[Dict[str, str]]] = {}

        # Human-readable names for specialists
        self.specialist_names = {
            "code_validation": "Code Validator",
            "rag_query": "Knowledge Base Assistant",
            "code_generation": "Code Generator",
            "code_analysis": "Code Analyst",
            "complex_reasoning": "Complex Reasoner",
            "general_chat": "General Assistant",
        }

        status = self.specialist_manager.get_status()
        logger.info(
            f"CoordinatorAgentService initialized with cloud-first specialists - "
            f"Anthropic: {status['anthropic']['available']}, "
            f"Google: {status['google']['available']}, "
            f"Local: {status['local']['available']}"
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
        self.sessions[session_id] = []
        logger.info(f"Created coordinator session: {session_id}")
        return session_id

    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> str:
        """
        Send a message and get a response via router-based cloud specialist delegation.

        Automatic cascading fallback: Anthropic → Google → Phi-3

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
                    categories, message, session_id
                )
                return self._aggregate_responses(categories, responses)
            else:
                # Single specialist execution
                return await self._run_single_specialist(
                    primary_agent, message, session_id
                )

        except Exception as e:
            logger.error(f"Error in coordinator chat: {e}", exc_info=True)
            logger.info("Falling back to general assistant due to error")
            return await self._fallback_to_general_assistant(message, session_id)

    async def _run_single_specialist(
        self,
        agent_type: str,
        message: str,
        session_id: str
    ) -> str:
        """
        Run a single specialist with cloud-first fallback.

        Args:
            agent_type: Specialist category
            message: User's message
            session_id: Session identifier

        Returns:
            Specialist's response string
        """
        logger.info(f"Delegating to specialist category: {agent_type}")

        try:
            # Get context for RAG queries
            context = ""
            if agent_type == "rag_query":
                context = await self._get_rag_context(message)

            # Execute with automatic fallback (Anthropic → Google → Phi-3)
            response = await self.specialist_manager.execute_with_fallback(
                specialist_type=agent_type,
                message=message,
                context=context
            )

            # Store in session history
            self._add_to_session(session_id, message, response)

            return response

        except Exception as e:
            logger.error(f"Specialist execution failed: {e}")
            return await self._fallback_to_general_assistant(message, session_id)

    async def _run_parallel_specialists(
        self,
        categories: List[str],
        message: str,
        session_id: str
    ) -> List[str]:
        """
        Run multiple specialists concurrently with cloud providers.

        Cloud providers enable TRUE parallelism (~600ms for 3 specialists)
        vs local sequential execution (~9s for 3 specialists)

        Args:
            categories: List of specialist categories
            message: User's message
            session_id: Session identifier

        Returns:
            List of specialist responses (successful only)
        """
        logger.info(f"Running {len(categories)} specialists in PARALLEL: {categories}")

        tasks = []
        for category in categories:
            # Get context for RAG queries
            context = ""
            if category == "rag_query":
                context_task = self._get_rag_context(message)
                context = await context_task

            # Create task for each specialist
            task = self.specialist_manager.execute_with_fallback(
                specialist_type=category,
                message=message,
                context=context
            )
            tasks.append(task)

        # Run in parallel - cloud APIs enable true concurrency!
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        successful_results = [
            r for r in results
            if isinstance(r, str) and r
        ]

        logger.info(
            f"Parallel execution completed: {len(successful_results)}/{len(tasks)} successful "
            f"(cloud parallel = fast!)"
        )

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
            specialist_name = self.specialist_names.get(
                category,
                category.replace("_", " ").title()
            )
            aggregated += f"**{specialist_name}:**\n{response}\n\n"

        return aggregated.strip()

    async def _get_rag_context(self, message: str) -> str:
        """
        Get RAG context for knowledge queries.

        Priority: Anthropic RAG > Google RAG > Local RAG

        Args:
            message: User's message

        Returns:
            Context string from RAG
        """
        try:
            # Try cloud RAG first for better quality
            if self.rag_anthropic_service:
                answer, _ = self.rag_anthropic_service.query(message, include_sources=False)
                return answer
            elif self.rag_google_service:
                answer, _ = self.rag_google_service.query(message, include_sources=False)
                return answer
            else:
                answer, _ = self.rag_service.query(message, include_sources=False)
                return answer
        except Exception as e:
            logger.warning(f"RAG context retrieval failed: {e}")
            return ""

    async def _fallback_to_general_assistant(
        self,
        message: str,
        session_id: str
    ) -> str:
        """
        Fallback to general assistant if routing or specialist fails.

        Args:
            message: User's message
            session_id: Session identifier

        Returns:
            General assistant's response
        """
        logger.warning("Using fallback: general_assistant")

        try:
            response = await self.specialist_manager.execute_with_fallback(
                specialist_type="general_chat",
                message=message,
                context=""
            )
            return response

        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
            return "I apologize, but I'm having trouble processing your request. Please try again."

    def _add_to_session(self, session_id: str, user_msg: str, assistant_msg: str):
        """Add messages to session history."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append({
            "role": "user",
            "content": user_msg
        })
        self.sessions[session_id].append({
            "role": "assistant",
            "content": assistant_msg
        })

    def get_specialist_status(self) -> dict:
        """Get status of all specialist providers."""
        return self.specialist_manager.get_status()

    def reset_circuit_breakers(self):
        """Reset all circuit breakers (for testing/recovery)."""
        self.specialist_manager.reset_circuit_breakers()