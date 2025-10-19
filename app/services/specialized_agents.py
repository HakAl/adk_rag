"""
Specialized agent factory for creating ADK agents.
"""
from typing import Optional, List
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from config import settings, logger
from app.tools import validate_code, create_rag_tools
from app.services.rag import RAGService
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService


class SpecializedAgentsFactory:
    """Factory for creating specialized agents."""

    def __init__(
            self,
            rag_service: RAGService,
            rag_anthropic_service: Optional[RAGAnthropicService] = None,
            rag_google_service: Optional[RAGGoogleService] = None
    ):
        self.rag_service = rag_service
        self.rag_anthropic_service = rag_anthropic_service
        self.rag_google_service = rag_google_service

        # Create models
        self.phi3_model = self._create_phi3_model()
        self.mistral_model = self._create_mistral_model()

        # Create RAG tools
        self.rag_tools = create_rag_tools(
            rag_service=rag_service,
            rag_anthropic_service=rag_anthropic_service,
            rag_google_service=rag_google_service
        )

        logger.info(f"SpecializedAgentsFactory initialized with {len(self.rag_tools)} RAG tools")

    def _create_phi3_model(self) -> LiteLlm:
        """Create phi3mini model instance (fast, for most agents)."""
        if settings.provider_type == "ollama":
            logger.info("Creating Phi-3 model via Ollama")
            return LiteLlm(
                model="ollama_chat/phi3:mini",
                supports_function_calling=True
            )
        else:  # llamacpp
            logger.info(f"Creating Phi-3 model via llama-server on port {settings.llama_server_port}")
            return LiteLlm(
                model="openai/phi3-fast",
                api_base=f"http://{settings.llama_server_host}:{settings.llama_server_port}/v1",
                api_key="dummy",
                supports_function_calling=True
            )

    def _create_mistral_model(self) -> LiteLlm:
        """Create mistral7b model instance (slower, for complex reasoning)."""
        if settings.provider_type == "ollama":
            logger.info("Creating Mistral-7B model via Ollama")
            return LiteLlm(
                model="ollama_chat/mistral",
                supports_function_calling=True
            )
        else:  # llamacpp
            logger.info(f"Creating Mistral-7B model via llama-server on port {settings.llama_server_mistral_port}")
            return LiteLlm(
                model="openai/mistral-smart",
                api_base=f"http://{settings.llama_server_host}:{settings.llama_server_mistral_port}/v1",
                api_key="dummy",
                supports_function_calling=True
            )

    def create_code_validation_agent(self) -> LlmAgent:
        """
        Create agent specialized in code syntax validation.

        Model: phi3mini (fast)
        Tools: validate_code only
        """
        return LlmAgent(
            name="code_validator",
            model=self.phi3_model,
            description="Validates code syntax for various programming languages including Python, JavaScript, TypeScript, JSON, HTML, CSS, XML, YAML, SQL, Go, Rust, Java, C, and C++.",
            instruction="""You are a code validation specialist. When a user provides code:

1. Identify the programming language (ask if unclear)
2. Use the validate_code tool to check syntax
3. Report results clearly and concisely
4. If there are errors, explain them simply

Be direct and helpful. Only validate syntax - do not generate or modify code.""",
            tools=[validate_code]
        )

    def create_rag_query_agent(self) -> LlmAgent:
        """
        Create agent specialized in knowledge base queries.

        Model: phi3mini (fast)
        Tools: All RAG tools (rag_query, rag_anthropic, rag_google)
        """
        # Build instruction based on available tools
        tool_guidance = "- rag_query: Fast local queries (use this by default)"

        if self.rag_anthropic_service:
            tool_guidance += "\n- rag_query_anthropic: Complex reasoning over documents (use for multi-step analysis)"

        if self.rag_google_service:
            tool_guidance += "\n- rag_query_google: Factual document queries (use for straightforward facts)"

        return LlmAgent(
            name="rag_assistant",
            model=self.phi3_model,
            description="Answers questions using the knowledge base. Retrieves and synthesizes information from documents.",
            instruction=f"""You are a knowledge base assistant. When a user asks a question:

1. Determine if the question requires information from the knowledge base
2. Choose the appropriate RAG tool:
{tool_guidance}

3. Query the knowledge base using the selected tool
4. Provide a clear answer with relevant information
5. If the knowledge base doesn't contain the answer, say so clearly

Always cite information when using the knowledge base.""",
            tools=self.rag_tools
        )

    def create_code_generation_agent(self) -> LlmAgent:
        """
        Create agent specialized in generating new code.

        Model: phi3mini (fast)
        Tools: validate_code only (to verify generated code)
        """
        return LlmAgent(
            name="code_generator",
            model=self.phi3_model,
            description="Generates new code based on requirements. Creates functions, classes, scripts, and programs in various languages.",
            instruction="""You are a code generation specialist. When asked to create code:

1. Clarify requirements if needed
2. Generate clean, well-structured code
3. Use the validate_code tool to verify syntax
4. Include comments explaining key parts
5. Provide usage examples when appropriate

Keep code simple and maintainable. Focus on correctness and clarity.""",
            tools=[validate_code]
        )

    def create_code_analysis_agent(self) -> LlmAgent:
        """
        Create agent specialized in analyzing and explaining code.

        Model: mistral7b (larger model for deeper analysis)
        Tools: validate_code + all RAG tools (for best practices/documentation)
        """
        all_tools = [validate_code] + self.rag_tools

        return LlmAgent(
            name="code_analyst",
            model=self.mistral_model,
            description="Analyzes, explains, and reviews code. Identifies issues, suggests improvements, and explains how code works.",
            instruction="""You are a code analysis specialist. When analyzing code:

1. Use validate_code to check syntax first
2. Explain what the code does step-by-step
3. Identify potential issues or improvements
4. Use RAG tools to reference best practices or documentation when relevant
5. Suggest optimizations or better approaches if appropriate

Be thorough but clear. Focus on helping the user understand the code.""",
            tools=all_tools
        )

    def create_complex_reasoning_agent(self) -> LlmAgent:
        """
        Create agent specialized in complex, multi-step reasoning.

        Model: mistral7b (larger model for better reasoning)
        Tools: ALL tools (may need any tool for complex problems)
        """
        all_tools = [validate_code] + self.rag_tools

        return LlmAgent(
            name="complex_reasoner",
            model=self.mistral_model,
            description="Handles complex, multi-step problems requiring deep reasoning, algorithms, mathematical analysis, or intricate logic.",
            instruction="""You are a complex reasoning specialist. For difficult problems:

1. Break down the problem into manageable steps
2. Use available tools as needed:
   - validate_code for code-related problems
   - RAG tools for retrieving relevant information
3. Show your reasoning process clearly
4. Verify your logic at each step
5. Provide a comprehensive solution

Take your time to think through complex problems thoroughly.""",
            tools=all_tools
        )

    def create_general_chat_agent(self) -> LlmAgent:
        """
        Create agent for general conversation.

        Model: phi3mini (fast for quick responses)
        Tools: None (pure conversation, no tool overhead)
        """
        return LlmAgent(
            name="general_assistant",
            model=self.phi3_model,
            description="Handles general conversation, greetings, simple questions, and casual chat. Provides quick, friendly responses.",
            instruction="""You are a helpful, friendly assistant. For general conversation:

1. Respond naturally and conversationally
2. Be concise but helpful
3. Answer simple questions directly using your knowledge
4. Keep responses brief for quick interactions
5. Be warm and approachable

You don't have access to tools - rely on your training for answers.""",
            tools=[]  # No tools for speed
        )

    def create_all_agents(self) -> List[LlmAgent]:
        """
        Create all 6 specialized agents.

        Returns:
            List of LlmAgent instances
        """
        agents = [
            self.create_code_validation_agent(),
            self.create_rag_query_agent(),
            self.create_code_generation_agent(),
            self.create_code_analysis_agent(),
            self.create_complex_reasoning_agent(),
            self.create_general_chat_agent()
        ]

        logger.info(f"Created {len(agents)} specialized agents")
        for agent in agents:
            tool_count = len(agent.tools) if agent.tools else 0
            model_name = "Mistral-7B" if agent.model == self.mistral_model else "Phi-3"
            logger.info(f"  - {agent.name}: {model_name}, {tool_count} tools")

        return agents