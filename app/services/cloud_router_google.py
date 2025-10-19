"""
Cloud router service using Google's Gemini API.
"""
import json
from typing import Dict, Any
import google.generativeai as genai

from config import settings, logger


class CloudRouterGoogleService:
    """Service for routing requests using Google Gemini."""

    def __init__(self):
        """Initialize Google cloud router service."""
        genai.configure(api_key=settings.google_api_key)
        self.model_name = settings.google_model
        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config={
                "temperature": 0.1,  # Low temperature for deterministic routing
                "max_output_tokens": 256,
            }
        )
        logger.info(f"CloudRouterGoogleService initialized with model: {self.model_name}")

    def route(self, message: str) -> Dict[str, Any]:
        """
        Route a message to appropriate agent(s) using Gemini.

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
        logger.info(f"[Google Router] Routing request: '{message[:100]}...'")

        try:
            prompt = self._build_routing_prompt(message)
            response = self._generate(prompt)
            routing_decision = self._parse_routing_response(response)

            logger.info(
                f"[Google Router] Decision: {routing_decision['primary_agent']} "
                f"(confidence: {routing_decision['confidence']:.2f})"
            )

            return routing_decision

        except Exception as e:
            logger.error(f"[Google Router] Routing error: {e}")
            return {
                "primary_agent": "general_chat",
                "parallel_agents": [],
                "confidence": 0.5,
                "reasoning": f"Routing failed: {str(e)}"
            }

    def _build_routing_prompt(self, message: str) -> str:
        """Build routing prompt optimized for Gemini."""
        return f"""You are a request classifier. Analyze the user's message and classify it into one of these categories.

Categories:
1. code_validation - Check syntax or validate code
2. rag_query - Questions needing information from documents/knowledge base
3. code_generation - Write/create new code
4. code_analysis - Explain or review existing code
5. complex_reasoning - Multi-step problems requiring deep thinking or algorithms
6. general_chat - Casual conversation, greetings, or simple questions

Guidelines:
- For SIMPLE requests, use ONE category as primary_agent with empty parallel_agents array
- For COMPLEX requests needing multiple perspectives, add relevant categories to parallel_agents
- Be confident and precise in your classification

Examples:
- "validate this code" → {{"primary_agent": "code_validation", "parallel_agents": [], "confidence": 0.95, "reasoning": "simple validation request"}}
- "validate and explain this code" → {{"primary_agent": "code_validation", "parallel_agents": ["code_analysis"], "confidence": 0.9, "reasoning": "needs validation and explanation"}}
- "is this code correct and how can I improve it?" → {{"primary_agent": "code_validation", "parallel_agents": ["code_analysis"], "confidence": 0.9, "reasoning": "validation plus improvement suggestions"}}
- "write a function" → {{"primary_agent": "code_generation", "parallel_agents": [], "confidence": 0.95, "reasoning": "straightforward code generation"}}
- "search docs for X" → {{"primary_agent": "rag_query", "parallel_agents": [], "confidence": 0.95, "reasoning": "knowledge base query"}}

User message: {message}

Output only valid JSON in this exact format (no markdown, no code blocks):
{{
    "primary_agent": "category_name",
    "parallel_agents": [],
    "confidence": 0.95,
    "reasoning": "brief explanation"
}}"""

    def _generate(self, prompt: str) -> str:
        """Generate routing response using Gemini."""
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def _parse_routing_response(self, response: str) -> Dict[str, Any]:
        """
        Parse routing response from Gemini.

        Args:
            response: Gemini's response text

        Returns:
            Routing decision dict
        """
        try:
            # Remove markdown code blocks if present
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
                if response.startswith("json"):
                    response = response[4:].strip()

            routing_data = json.loads(response)

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
            logger.error(f"[Google Router] JSON decode error: {e}\nResponse: {response}")
            raise ValueError(f"Invalid JSON in routing response: {e}")
        except Exception as e:
            logger.error(f"[Google Router] Error parsing routing response: {e}")
            raise