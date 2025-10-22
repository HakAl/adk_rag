"""
Router service for analyzing and classifying incoming requests.
Supports both local llama.cpp routing and cloud-based routing via Anthropic/Google.
"""
import json
from typing import Optional, Dict, Any
from pathlib import Path

from config import settings, logger

# Gate llama_cpp imports for production
if settings.environment != "production":
    try:
        from llama_cpp import Llama, LlamaGrammar
        LLAMA_CPP_AVAILABLE = True
    except ImportError:
        LLAMA_CPP_AVAILABLE = False
        logger.warning("llama_cpp not available for local routing")
else:
    LLAMA_CPP_AVAILABLE = False


class RouterService:
    """Service for routing requests to appropriate agents."""

    # JSON grammar for llama.cpp to enforce valid routing response
    ROUTING_GRAMMAR = r'''
root ::= routing-object
routing-object ::= "{" ws "\"primary_agent\"" ws ":" ws string ws "," ws "\"parallel_agents\"" ws ":" ws array ws "," ws "\"confidence\"" ws ":" ws number ws "," ws "\"reasoning\"" ws ":" ws string ws "}"

string ::= "\"" ([^"\\\n] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F]))* "\""
number ::= "-"? ("0" | [1-9] [0-9]*) ("." [0-9]+)? ([eE] [-+]? [0-9]+)?
array ::= "[" ws (string (ws "," ws string)*)? ws "]"
ws ::= [ \t\n]*
'''

    def __init__(self):
        """Initialize router service with cloud or local routing."""
        self.enabled = self._check_enabled()
        self.llm = None
        self.cloud_router = None
        self.router_type = None

        if self.enabled:
            # Try cloud routers first (Anthropic preferred over Google)
            if settings.anthropic_api_key:
                self._initialize_cloud_router_anthropic()
            elif settings.google_api_key:
                self._initialize_cloud_router_google()
            else:
                # Fall back to local router only in non-production
                if settings.environment != "production":
                    self._initialize_llm()
                else:
                    logger.warning("Local router not available in production - cloud routing required")
                    self.enabled = False
        else:
            logger.info("RouterService disabled - no router configured")

    def _check_enabled(self) -> bool:
        """
        Check if router is enabled.

        Router is enabled if EITHER:
        1. Cloud API keys are available (Anthropic or Google), OR
        2. Local router model path is configured (non-production only)
        """
        has_cloud = bool(settings.anthropic_api_key or settings.google_api_key)

        # Only check local model in non-production
        has_local = False
        if settings.environment != "production":
            has_local = bool(
                LLAMA_CPP_AVAILABLE and
                settings.router_model_path and
                Path(settings.router_model_path).exists()
            )

        return has_cloud or has_local

    def _initialize_cloud_router_anthropic(self):
        """Initialize Anthropic cloud router."""
        try:
            from app.services.cloud_router_anthropic import CloudRouterAnthropicService

            self.cloud_router = CloudRouterAnthropicService()
            self.router_type = "anthropic"
            logger.info("✓ RouterService enabled with Anthropic Claude (cloud-based routing)")

        except Exception as e:
            logger.error(f"Failed to initialize Anthropic cloud router: {e}")
            # Try Google as fallback
            if settings.google_api_key:
                self._initialize_cloud_router_google()
            else:
                self.enabled = False

    def _initialize_cloud_router_google(self):
        """Initialize Google cloud router."""
        try:
            from app.services.cloud_router_google import CloudRouterGoogleService

            self.cloud_router = CloudRouterGoogleService()
            self.router_type = "google"
            logger.info("✓ RouterService enabled with Google Gemini (cloud-based routing)")

        except Exception as e:
            logger.error(f"Failed to initialize Google cloud router: {e}")
            self.enabled = False

    def _initialize_llm(self):
        """Initialize the local router LLM (non-production only)."""
        if settings.environment == "production":
            logger.error("Cannot initialize local LLM in production environment")
            self.enabled = False
            return

        if not LLAMA_CPP_AVAILABLE:
            logger.error("llama_cpp not available for local routing")
            self.enabled = False
            return

        try:
            self.llm = Llama(
                model_path=settings.router_model_path,
                n_ctx=settings.router_n_ctx,
                n_batch=settings.router_n_batch,
                n_threads=settings.router_n_threads,
                temperature=settings.router_temperature,
                verbose=settings.debug
            )
            self.router_type = "local"
            logger.info(f"✓ RouterService enabled with local model: {settings.router_model_path}")

        except Exception as e:
            logger.error(f"Failed to initialize local router LLM: {e}")
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
            # Delegate to cloud router if available
            if self.cloud_router:
                return self.cloud_router.route(message)

            # Otherwise use local router (non-production only)
            if settings.environment == "production":
                logger.error("Local routing attempted in production environment")
                return {
                    "primary_agent": "general_chat",
                    "parallel_agents": [],
                    "confidence": 0.5,
                    "reasoning": "Local routing not available in production"
                }

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
        """Build prompt for local routing classification."""
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
        """Generate response from local router LLM with JSON grammar enforcement."""
        if settings.environment == "production":
            raise RuntimeError("Local generation not available in production")

        if not LLAMA_CPP_AVAILABLE:
            raise RuntimeError("llama_cpp not available")

        # Create grammar object to enforce JSON structure
        grammar = LlamaGrammar.from_string(self.ROUTING_GRAMMAR)

        response = self.llm(
            prompt,
            max_tokens=settings.router_max_tokens,
            temperature=settings.router_temperature,
            grammar=grammar,  # Enforce valid JSON output
            stop=["<|end|>", "<|assistant|>", "<|user|>", "User message:", "\n\n\n"]
        )

        return response['choices'][0]['text'].strip()

    def _parse_routing_response(self, response: str) -> Dict[str, Any]:
        """
        Parse routing response from local LLM.

        Args:
            response: LLM response text

        Returns:
            Routing decision dict
        """
        try:
            # With grammar enforcement, response should be clean JSON
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