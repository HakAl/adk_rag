"""
Coordinator Agent service with cloud-first specialist delegation using router-based classification.
"""
import asyncio
import uuid
from typing import Optional, Dict, Any, List, AsyncGenerator

from google.genai import types

from config import settings, logger
from app.services.rag import RAGService
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService
from app.services.router import RouterService
from app.services.specialist_manager import SpecialistManager
from app.db.session_service import PostgreSQLSessionService


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

        # Use PostgreSQL session service
        self.session_service = PostgreSQLSessionService()

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
        await self.session_service.create_session(
            app_name="coordinator",
            user_id=user_id,
            session_id=session_id,
            agent_type="coordinator"
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

        # FIXED: Ensure session exists before processing
        await self._ensure_session_exists(session_id, user_id)

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

    async def chat_stream(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a message and stream the response with routing info.

        Args:
            message: User's message
            user_id: User identifier
            session_id: Session identifier

        Yields:
            Event dictionaries with type and data
        """
        logger.info(f"Processing streaming coordinator chat for session {session_id}")

        # Ensure session exists
        await self._ensure_session_exists(session_id, user_id)

        try:
            # Route to appropriate specialist(s)
            routing_decision = self.router_service.route(message)
            primary_agent = routing_decision["primary_agent"]
            confidence = routing_decision["confidence"]
            reasoning = routing_decision.get("reasoning", "")

            logger.info(
                f"Router classified as '{primary_agent}' (confidence: {confidence:.2f})"
            )

            # Yield routing info immediately
            specialist_name = self.specialist_names.get(
                primary_agent,
                primary_agent.replace("_", " ").title()
            )

            yield {
                "type": "routing",
                "data": {
                    "agent": primary_agent,
                    "agent_name": specialist_name,
                    "confidence": confidence,
                    "reasoning": reasoning
                }
            }

            # Stream specialist response
            full_response = ""
            async for chunk in self._run_streaming_specialist(
                primary_agent, message, session_id
            ):
                full_response += chunk
                yield {
                    "type": "content",
                    "data": chunk
                }

            # Store in session history
            await self._add_to_session(session_id, message, full_response)

            # Yield completion event
            yield {
                "type": "done",
                "data": {"message": "Response complete"}
            }

        except Exception as e:
            logger.error(f"Error in coordinator streaming: {e}", exc_info=True)
            yield {
                "type": "error",
                "data": {"message": str(e)}
            }

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
                app_name="coordinator",
                user_id=user_id,
                session_id=session_id,
                agent_type="coordinator"
            )

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
            await self._add_to_session(session_id, message, response)

            return response

        except Exception as e:
            logger.error(f"Specialist execution failed: {e}")
            return await self._fallback_to_general_assistant(message, session_id)

    async def _run_streaming_specialist(
        self,
        agent_type: str,
        message: str,
        session_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Run a single specialist with streaming response.

        Args:
            agent_type: Specialist category
            message: User's message
            session_id: Session identifier

        Yields:
            Text chunks from specialist
        """
        logger.info(f"Streaming from specialist category: {agent_type}")

        try:
            # Get context for RAG queries
            context = ""
            if agent_type == "rag_query":
                context = await self._get_rag_context(message)

            # Execute with streaming and automatic fallback
            async for chunk in self.specialist_manager.execute_stream_with_fallback(
                specialist_type=agent_type,
                message=message,
                context=context
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Streaming specialist execution failed: {e}")
            # Fallback to non-streaming general assistant
            response = await self._fallback_to_general_assistant(message, session_id)
            yield response

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

    async def _add_to_session(self, session_id: str, user_msg: str, assistant_msg: str):
        """Add messages to session history in database."""
        await self.session_service.save_message(session_id, "user", user_msg)
        await self.session_service.save_message(session_id, "assistant", assistant_msg)

    def get_specialist_status(self) -> dict:
        """Get status of all specialist providers."""
        return self.specialist_manager.get_status()

    def reset_circuit_breakers(self):
        """Reset all circuit breakers (for testing/recovery)."""
        self.specialist_manager.reset_circuit_breakers()