"""
Router service for analyzing and classifying incoming requests.
"""
import json
from typing import Optional, Dict, Any
from pathlib import Path

from config import settings, logger


class RouterService:
    """Service for routing requests to appropriate agents."""

    def __init__(self):
        """Initialize router service."""
        self.enabled = self._check_enabled()
        self.llm = None

        if self.enabled:
            self._initialize_llm()
            logger.info(f"RouterService enabled with model: {settings.router_model_path}")
        else:
            logger.info("RouterService disabled - ROUTER_MODEL_PATH not configured")

    def _check_enabled(self) -> bool:
        """Check if router is enabled based on configuration."""
        return bool(settings.router_model_path and Path(settings.router_model_path).exists())

    def _initialize_llm(self):
        """Initialize the router LLM."""
        try:
            from llama_cpp import Llama

            self.llm = Llama(
                model_path=settings.router_model_path,
                n_ctx=settings.router_n_ctx,
                n_batch=settings.router_n_batch,
                n_threads=settings.router_n_threads,
                temperature=settings.router_temperature,
                verbose=settings.debug
            )
            logger.info("Router LLM initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize router LLM: {e}")
            self.enabled = False

    def route(self, message: str) -> Dict[str, Any]:
        """
        Route a message to appropriate agent(s).

        Args:
            message: User's message

        Returns:
            Dict with routing decision:
            {
                "primary_agent": str,
                "parallel_agents": list,
                "confidence": float,
                "reasoning": str
            }
        """
        if not self.enabled:
            # Default routing when router is disabled
            return {
                "primary_agent": "general_chat",
                "parallel_agents": [],
                "confidence": 1.0,
                "reasoning": "Router disabled - using default agent"
            }

        logger.info(f"Routing request: '{message[:100]}...'")

        try:
            prompt = self._build_routing_prompt(message)
            response = self._generate(prompt)
            routing_decision = self._parse_routing_response(response)

            logger.info(
                f"Routing decision: {routing_decision['primary_agent']} "
                f"(confidence: {routing_decision['confidence']:.2f})"
            )

            return routing_decision

        except Exception as e:
            logger.error(f"Routing error: {e}")
            # Fallback to general chat on error
            return {
                "primary_agent": "general_chat",
                "parallel_agents": [],
                "confidence": 0.5,
                "reasoning": f"Routing failed: {str(e)}"
            }

    def _build_routing_prompt(self, message: str) -> str:
        """Build prompt for routing classification."""
        return f"""You are a request classifier. Analyze the user's message and classify it.

Categories:
1. code_validation - Check syntax or validate code
2. rag_query - Questions needing information from documents/knowledge base
3. code_generation - Write/create new code
4. code_analysis - Explain or review existing code
5. complex_reasoning - Multi-step problems requiring deep thinking or algorithms
6. general_chat - Casual conversation, greetings, or simple questions

For SIMPLE requests, use ONE category as primary_agent with empty parallel_agents.
For COMPLEX requests needing multiple perspectives, add relevant categories to parallel_agents.

Examples:
- "validate this code" → {{"primary_agent": "code_validation", "parallel_agents": [], "confidence": 0.95, "reasoning": "simple validation request"}}
- "validate and explain this code" → {{"primary_agent": "code_validation", "parallel_agents": ["code_analysis"], "confidence": 0.9, "reasoning": "needs validation and explanation"}}
- "is this code correct and how can I improve it?" → {{"primary_agent": "code_validation", "parallel_agents": ["code_analysis"], "confidence": 0.9, "reasoning": "validation plus improvement suggestions"}}
- "write a function" → {{"primary_agent": "code_generation", "parallel_agents": [], "confidence": 0.95, "reasoning": "straightforward code generation"}}
- "search docs for X" → {{"primary_agent": "rag_query", "parallel_agents": [], "confidence": 0.95, "reasoning": "knowledge base query"}}

User message: {message}

Respond ONLY with valid JSON in this exact format:
{{
    "primary_agent": "category_name",
    "parallel_agents": [],
    "confidence": 0.95,
    "reasoning": "brief explanation"
}}

JSON Response:"""

    def _generate(self, prompt: str) -> str:
        """Generate response from router LLM."""
        response = self.llm(
            prompt,
            max_tokens=settings.router_max_tokens,
            temperature=settings.router_temperature,
            stop=["<|end|>", "<|assistant|>", "<|user|>", "User message:", "\n\n\n"]
        )

        return response['choices'][0]['text'].strip()

    def _parse_routing_response(self, response: str) -> Dict[str, Any]:
        """
        Parse routing response from LLM.

        Args:
            response: LLM response text

        Returns:
            Routing decision dict
        """
        try:
            # Extract FIRST complete JSON object only
            json_start = response.find('{')
            if json_start == -1:
                raise ValueError("No JSON found in response")

            # Find the matching closing brace for the first opening brace
            brace_count = 0
            json_end = -1

            for i in range(json_start, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if json_end == -1:
                raise ValueError("No complete JSON object found in response")

            json_str = response[json_start:json_end]
            routing_data = json.loads(json_str)

            # Validate required fields
            required_fields = ["primary_agent", "parallel_agents", "confidence", "reasoning"]
            for field in required_fields:
                if field not in routing_data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate agent category
            valid_agents = [
                "code_validation",
                "rag_query",
                "code_generation",
                "code_analysis",
                "complex_reasoning",
                "general_chat"
            ]

            if routing_data["primary_agent"] not in valid_agents:
                logger.warning(
                    f"Invalid agent category: {routing_data['primary_agent']}, "
                    f"defaulting to general_chat"
                )
                routing_data["primary_agent"] = "general_chat"

            # Ensure confidence is a float between 0 and 1
            routing_data["confidence"] = max(0.0, min(1.0, float(routing_data["confidence"])))

            # Ensure parallel_agents is a list
            if not isinstance(routing_data["parallel_agents"], list):
                routing_data["parallel_agents"] = []

            return routing_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}\nResponse: {response}")
            raise ValueError(f"Invalid JSON in routing response: {e}")
        except Exception as e:
            logger.error(f"Error parsing routing response: {e}")
            raise

    def get_agent_description(self, agent_type: str) -> str:
        """
        Get human-readable description of agent type.

        Args:
            agent_type: Agent category

        Returns:
            Description string
        """
        descriptions = {
            "code_validation": "Code syntax validation and checking",
            "rag_query": "Knowledge base query and document retrieval",
            "code_generation": "New code generation and creation",
            "code_analysis": "Code explanation and review",
            "complex_reasoning": "Complex problem solving and algorithms",
            "general_chat": "General conversation and assistance"
        }

        return descriptions.get(agent_type, "Unknown agent type")