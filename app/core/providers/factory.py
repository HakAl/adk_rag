"""
Factory for creating model providers.
"""
from typing import Optional
from .base import ModelProvider
from .ollama_provider import OllamaProvider
from .llamacpp_provider import LlamaCppProvider


class ProviderFactory:
    """Factory for creating model providers."""

    @staticmethod
    def create_provider(
            provider_type: str,
            **kwargs
    ) -> ModelProvider:
        """
        Create a model provider instance.

        Args:
            provider_type: Type of provider ('ollama' or 'llamacpp')
            **kwargs: Provider-specific configuration

        Returns:
            ModelProvider instance

        Raises:
            ValueError: If provider_type is not supported
        """
        provider_type = provider_type.lower()

        if provider_type == 'ollama':
            return ProviderFactory._create_ollama(**kwargs)
        elif provider_type in ['llamacpp', 'llama.cpp', 'llama_cpp']:
            return ProviderFactory._create_llamacpp(**kwargs)
        else:
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported types: 'ollama', 'llamacpp'"
            )

    @staticmethod
    def _create_ollama(**kwargs) -> OllamaProvider:
        """Create Ollama provider."""
        required = ['embedding_model', 'chat_model', 'base_url']
        for param in required:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter for Ollama: {param}")

        return OllamaProvider(
            embedding_model=kwargs['embedding_model'],
            chat_model=kwargs['chat_model'],
            base_url=kwargs['base_url'],
            debug=kwargs.get('debug', False)
        )

    @staticmethod
    def _create_llamacpp(**kwargs) -> LlamaCppProvider:
        """Create llama.cpp provider."""
        required = ['embedding_model_path', 'chat_model_path']
        for param in required:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter for llama.cpp: {param}")

        return LlamaCppProvider(
            embedding_model_path=kwargs['embedding_model_path'],
            chat_model_path=kwargs['chat_model_path'],
            n_ctx=kwargs.get('n_ctx', 2048),
            n_batch=kwargs.get('n_batch', 512),
            n_threads=kwargs.get('n_threads'),
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 512),
            verbose=kwargs.get('verbose', False)
        )