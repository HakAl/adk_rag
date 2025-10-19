"""
Specialist manager with intelligent fallback and circuit breaker.
"""
from typing import Optional, Union, AsyncGenerator
from pathlib import Path

from config import settings, logger
from app.services.circuit_breaker import CircuitBreaker
from app.services.cloud_specialist_anthropic import CloudSpecialistAnthropicService
from app.services.cloud_specialist_google import CloudSpecialistGoogleService
from app.services.local_specialist_phi3 import LocalSpecialistPhi3Service


class SpecialistManager:
    """
    Manages specialists with intelligent fallback.

    Priority:
    1. Anthropic (cloud, fast, smart)
    2. Google (cloud, fast, smart)
    3. Phi-3 (local, slower, reliable)
    """

    def __init__(self):
        """Initialize specialist manager with circuit breakers."""
        # Circuit breakers for each provider
        self.anthropic_breaker = CircuitBreaker(
            name="Anthropic",
            failure_threshold=5,
            timeout=60
        )
        self.google_breaker = CircuitBreaker(
            name="Google",
            failure_threshold=5,
            timeout=60
        )

        # Check provider availability
        self.has_anthropic = bool(settings.anthropic_api_key)
        self.has_google = bool(settings.google_api_key)
        self.has_local = bool(
            settings.llamacpp_chat_model_path and
            Path(settings.llamacpp_chat_model_path).exists()
        )

        # Shared Phi-3 model (lazy loaded)
        self._phi3_model = None

        logger.info(
            f"SpecialistManager initialized - "
            f"Anthropic: {self.has_anthropic}, "
            f"Google: {self.has_google}, "
            f"Local: {self.has_local}"
        )

    async def get_specialist(
            self,
            specialist_type: str
    ) -> Union[CloudSpecialistAnthropicService, CloudSpecialistGoogleService, LocalSpecialistPhi3Service]:
        """
        Get best available specialist with cascading fallback.

        Args:
            specialist_type: Type of specialist needed

        Returns:
            Specialist service instance

        Raises:
            RuntimeError: If no specialists available
        """
        # Try Anthropic first
        if self.has_anthropic and not self.anthropic_breaker.is_open():
            try:
                specialist = CloudSpecialistAnthropicService(specialist_type)
                logger.debug(f"Using Anthropic specialist: {specialist_type}")
                return specialist
            except Exception as e:
                logger.warning(f"Anthropic specialist creation failed: {e}")
                self.anthropic_breaker.record_failure()

        # Try Google second
        if self.has_google and not self.google_breaker.is_open():
            try:
                specialist = CloudSpecialistGoogleService(specialist_type)
                logger.debug(f"Using Google specialist: {specialist_type}")
                return specialist
            except Exception as e:
                logger.warning(f"Google specialist creation failed: {e}")
                self.google_breaker.record_failure()

        # Fallback to local Phi-3
        if self.has_local:
            try:
                # Load shared model if not already loaded
                if self._phi3_model is None:
                    logger.info("Loading shared Phi-3 model for local specialists")
                    from llama_cpp import Llama
                    self._phi3_model = Llama(
                        model_path=settings.llamacpp_chat_model_path,
                        n_ctx=settings.llamacpp_n_ctx,
                        n_batch=settings.llamacpp_n_batch,
                        n_threads=settings.llamacpp_n_threads,
                        temperature=settings.llamacpp_temperature,
                        verbose=settings.debug
                    )

                specialist = LocalSpecialistPhi3Service(specialist_type, self._phi3_model)
                logger.debug(f"Using local Phi-3 specialist: {specialist_type}")
                return specialist
            except Exception as e:
                logger.error(f"Local specialist creation failed: {e}")
                raise RuntimeError(f"Failed to create local specialist: {e}")

        # No specialists available
        raise RuntimeError(
            f"No specialists available for {specialist_type}. "
            f"Anthropic: {'circuit open' if self.anthropic_breaker.is_open() else 'unavailable'}, "
            f"Google: {'circuit open' if self.google_breaker.is_open() else 'unavailable'}, "
            f"Local: unavailable"
        )

    async def execute_with_fallback(
            self,
            specialist_type: str,
            message: str,
            context: str = ""
    ) -> str:
        """
        Execute specialist task with automatic fallback on failure.

        Args:
            specialist_type: Type of specialist
            message: User's message
            context: Additional context

        Returns:
            Specialist's response

        Raises:
            RuntimeError: If all specialists fail
        """
        # Try Anthropic
        if self.has_anthropic and not self.anthropic_breaker.is_open():
            try:
                specialist = CloudSpecialistAnthropicService(specialist_type)
                response = await specialist.execute(message, context)
                self.anthropic_breaker.record_success()
                return response
            except Exception as e:
                logger.warning(f"Anthropic execution failed: {e}")
                self.anthropic_breaker.record_failure()

        # Try Google
        if self.has_google and not self.google_breaker.is_open():
            try:
                specialist = CloudSpecialistGoogleService(specialist_type)
                response = await specialist.execute(message, context)
                self.google_breaker.record_success()
                return response
            except Exception as e:
                logger.warning(f"Google execution failed: {e}")
                self.google_breaker.record_failure()

        # Try local
        if self.has_local:
            try:
                # Load shared model if not already loaded
                if self._phi3_model is None:
                    logger.info("Loading shared Phi-3 model for fallback")
                    from llama_cpp import Llama
                    self._phi3_model = Llama(
                        model_path=settings.llamacpp_chat_model_path,
                        n_ctx=settings.llamacpp_n_ctx,
                        n_batch=settings.llamacpp_n_batch,
                        n_threads=settings.llamacpp_n_threads,
                        temperature=settings.llamacpp_temperature,
                        verbose=settings.debug
                    )

                specialist = LocalSpecialistPhi3Service(specialist_type, self._phi3_model)
                response = await specialist.execute(message, context)
                return response
            except Exception as e:
                logger.error(f"Local execution failed: {e}")
                raise RuntimeError(f"All specialists failed for {specialist_type}")

        raise RuntimeError("No specialists available")

    async def execute_stream_with_fallback(
            self,
            specialist_type: str,
            message: str,
            context: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        Execute specialist task with streaming and automatic fallback.

        Args:
            specialist_type: Type of specialist
            message: User's message
            context: Additional context

        Yields:
            Text chunks as they arrive from specialist

        Raises:
            RuntimeError: If all specialists fail
        """
        # Try Anthropic
        if self.has_anthropic and not self.anthropic_breaker.is_open():
            try:
                specialist = CloudSpecialistAnthropicService(specialist_type)
                async for chunk in specialist.execute_stream(message, context):
                    yield chunk
                self.anthropic_breaker.record_success()
                return  # Success, exit
            except Exception as e:
                logger.warning(f"Anthropic streaming failed: {e}")
                self.anthropic_breaker.record_failure()

        # Try Google
        if self.has_google and not self.google_breaker.is_open():
            try:
                specialist = CloudSpecialistGoogleService(specialist_type)
                async for chunk in specialist.execute_stream(message, context):
                    yield chunk
                self.google_breaker.record_success()
                return  # Success, exit
            except Exception as e:
                logger.warning(f"Google streaming failed: {e}")
                self.google_breaker.record_failure()

        # Try local
        if self.has_local:
            try:
                # Load shared model if not already loaded
                if self._phi3_model is None:
                    logger.info("Loading shared Phi-3 model for streaming fallback")
                    from llama_cpp import Llama
                    self._phi3_model = Llama(
                        model_path=settings.llamacpp_chat_model_path,
                        n_ctx=settings.llamacpp_n_ctx,
                        n_batch=settings.llamacpp_n_batch,
                        n_threads=settings.llamacpp_n_threads,
                        temperature=settings.llamacpp_temperature,
                        verbose=settings.debug
                    )

                specialist = LocalSpecialistPhi3Service(specialist_type, self._phi3_model)
                async for chunk in specialist.execute_stream(message, context):
                    yield chunk
                return  # Success, exit
            except Exception as e:
                logger.error(f"Local streaming failed: {e}")
                raise RuntimeError(f"All specialists failed for {specialist_type}")

        raise RuntimeError("No specialists available for streaming")

    def get_status(self) -> dict:
        """Get status of all providers."""
        return {
            "anthropic": {
                "available": self.has_anthropic,
                "circuit_state": self.anthropic_breaker.get_state()
            },
            "google": {
                "available": self.has_google,
                "circuit_state": self.google_breaker.get_state()
            },
            "local": {
                "available": self.has_local,
                "model_loaded": self._phi3_model is not None
            }
        }

    def reset_circuit_breakers(self):
        """Manually reset all circuit breakers."""
        self.anthropic_breaker.reset()
        self.google_breaker.reset()
        logger.info("All circuit breakers reset")