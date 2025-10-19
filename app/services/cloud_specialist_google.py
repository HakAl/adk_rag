"""
Cloud specialist service using Google's Gemini API.
"""
import asyncio
from typing import Dict, Any
import google.generativeai as genai
from google.api_core import exceptions

from config import settings, logger


class CloudSpecialistGoogleService:
    """Service for specialist tasks using Google Gemini."""

    # Specialist-specific prompts optimized for Gemini
    SPECIALIST_PROMPTS = {
        "code_validation": """You are a code validation specialist. Your task is to:
1. Check for syntax errors
2. Identify potential bugs or issues
3. Verify code follows best practices
4. Provide clear, actionable feedback

Be concise and focus on correctness.""",

        "code_generation": """You are a code generation specialist. Your task is to:
1. Write clean, efficient, well-documented code
2. Follow best practices and design patterns
3. Include error handling where appropriate
4. Explain key design decisions

Generate production-ready code.""",

        "code_analysis": """You are a code analysis specialist. Your task is to:
1. Explain what the code does clearly
2. Identify the purpose and logic flow
3. Point out strengths and potential improvements
4. Suggest optimizations if applicable

Provide insightful analysis.""",

        "rag_query": """You are a knowledge base specialist. Your task is to:
1. Answer questions using only the provided context
2. Be precise and cite specific information
3. Admit when information is not in the context
4. Provide comprehensive but concise answers

Focus on accuracy and relevance.""",

        "complex_reasoning": """You are a complex reasoning specialist. Your task is to:
1. Break down complex problems into steps
2. Apply logical reasoning and analysis
3. Consider edge cases and alternatives
4. Provide well-reasoned solutions

Think deeply and systematically.""",

        "general_chat": """You are a helpful assistant. Your task is to:
1. Provide friendly, conversational responses
2. Be clear and concise
3. Anticipate follow-up questions
4. Maintain a positive, professional tone

Be helpful and engaging."""
    }

    def __init__(self, specialist_type: str):
        """
        Initialize Google cloud specialist.

        Args:
            specialist_type: Type of specialist (code_validation, etc.)
        """
        self.specialist_type = specialist_type
        genai.configure(api_key=settings.google_api_key)
        self.model_name = settings.google_model

        system_instruction = self.SPECIALIST_PROMPTS.get(
            specialist_type,
            self.SPECIALIST_PROMPTS["general_chat"]
        )

        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
            system_instruction=system_instruction
        )
        logger.info(f"CloudSpecialistGoogle initialized: {specialist_type}")

    async def execute(
            self,
            message: str,
            context: str = "",
            retries: int = 3
    ) -> str:
        """
        Execute specialist task with retry logic.

        Args:
            message: User's message/request
            context: Additional context (e.g., RAG results)
            retries: Number of retry attempts

        Returns:
            Specialist's response
        """
        for attempt in range(retries):
            try:
                response = await self._call_gemini(message, context)
                return response

            except exceptions.ResourceExhausted as e:
                logger.warning(
                    f"[Google {self.specialist_type}] Rate limit hit (attempt {attempt + 1}/{retries}): {e}"
                )
                if attempt < retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Out of retries, raise to trigger fallback
                    raise

            except Exception as e:
                logger.error(f"[Google {self.specialist_type}] API error: {e}")
                raise

    async def _call_gemini(self, message: str, context: str = "") -> str:
        """
        Make API call to Google Gemini.

        Args:
            message: User's message
            context: Additional context

        Returns:
            Gemini's response
        """
        # Build the user message
        user_message = message
        if context:
            user_message = f"Context:\n{context}\n\nUser Request:\n{message}"

        # Make synchronous call in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.model.generate_content(user_message)
        )

        return response.text.strip()

    def get_specialist_name(self) -> str:
        """Get human-readable specialist name."""
        names = {
            "code_validation": "Code Validator (Gemini)",
            "code_generation": "Code Generator (Gemini)",
            "code_analysis": "Code Analyst (Gemini)",
            "rag_query": "Knowledge Assistant (Gemini)",
            "complex_reasoning": "Reasoning Specialist (Gemini)",
            "general_chat": "General Assistant (Gemini)"
        }
        return names.get(self.specialist_type, f"{self.specialist_type} (Gemini)")