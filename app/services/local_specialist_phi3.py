"""
Local specialist service using Phi-3 via llama.cpp.
"""
import asyncio
from typing import Optional
from llama_cpp import Llama

from config import settings, logger


class LocalSpecialistPhi3Service:
    """Service for specialist tasks using local Phi-3 model."""

    # Specialist-specific prompts
    SPECIALIST_PROMPTS = {
        "code_validation": """<|system|>
You are a code validation specialist. Check for syntax errors, bugs, and best practices. Be concise.<|end|>
<|user|>
{message}<|end|>
<|assistant|>""",

        "code_generation": """<|system|>
You are a code generation specialist. Write clean, efficient, well-documented code following best practices.<|end|>
<|user|>
{message}<|end|>
<|assistant|>""",

        "code_analysis": """<|system|>
You are a code analysis specialist. Explain what code does, identify strengths and improvements.<|end|>
<|user|>
{message}<|end|>
<|assistant|>""",

        "rag_query": """<|system|>
You are a knowledge base specialist. Answer using only the provided context. Be precise and cite sources.<|end|>
<|user|>
Context:
{context}

Question: {message}<|end|>
<|assistant|>""",

        "complex_reasoning": """<|system|>
You are a reasoning specialist. Break down complex problems, apply logic, and provide well-reasoned solutions.<|end|>
<|user|>
{message}<|end|>
<|assistant|>""",

        "general_chat": """<|system|>
You are a helpful assistant. Provide clear, friendly, and professional responses.<|end|>
<|user|>
{message}<|end|>
<|assistant|>"""
    }

    def __init__(self, specialist_type: str, model: Optional[Llama] = None):
        """
        Initialize local Phi-3 specialist.

        Args:
            specialist_type: Type of specialist (code_validation, etc.)
            model: Optional pre-loaded Llama model (for sharing)
        """
        self.specialist_type = specialist_type
        self.prompt_template = self.SPECIALIST_PROMPTS.get(
            specialist_type,
            self.SPECIALIST_PROMPTS["general_chat"]
        )

        # Use shared model or load new one
        if model:
            self.model = model
            logger.info(f"LocalSpecialistPhi3 using shared model: {specialist_type}")
        else:
            self.model = self._load_model()
            logger.info(f"LocalSpecialistPhi3 loaded new model: {specialist_type}")

    def _load_model(self) -> Llama:
        """Load Phi-3 model."""
        return Llama(
            model_path=settings.llamacpp_chat_model_path,
            n_ctx=settings.llamacpp_n_ctx,
            n_batch=settings.llamacpp_n_batch,
            n_threads=settings.llamacpp_n_threads,
            temperature=settings.llamacpp_temperature,
            verbose=settings.debug
        )

    async def execute(
            self,
            message: str,
            context: str = ""
    ) -> str:
        """
        Execute specialist task using local Phi-3.

        Args:
            message: User's message/request
            context: Additional context (e.g., RAG results)

        Returns:
            Specialist's response
        """
        try:
            # Build prompt with context if provided
            if context and "{context}" in self.prompt_template:
                prompt = self.prompt_template.format(message=message, context=context)
            else:
                prompt = self.prompt_template.format(message=message)

            # Run inference in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._generate(prompt)
            )

            return response

        except Exception as e:
            logger.error(f"[Local Phi-3 {self.specialist_type}] Error: {e}")
            raise

    def _generate(self, prompt: str) -> str:
        """Generate response using Phi-3."""
        response = self.model(
            prompt,
            max_tokens=settings.llamacpp_max_tokens,
            temperature=settings.llamacpp_temperature,
            stop=["<|end|>", "<|user|>", "<|system|>"]
        )

        return response['choices'][0]['text'].strip()

    def get_specialist_name(self) -> str:
        """Get human-readable specialist name."""
        names = {
            "code_validation": "Code Validator (Phi-3)",
            "code_generation": "Code Generator (Phi-3)",
            "code_analysis": "Code Analyst (Phi-3)",
            "rag_query": "Knowledge Assistant (Phi-3)",
            "complex_reasoning": "Reasoning Specialist (Phi-3)",
            "general_chat": "General Assistant (Phi-3)"
        }
        return names.get(self.specialist_type, f"{self.specialist_type} (Phi-3)")