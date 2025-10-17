"""
Base classes for model providers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    def get_embeddings(self):
        """
        Get embeddings instance compatible with LangChain.

        Returns:
            LangChain embeddings object
        """
        pass


class ChatProvider(ABC):
    """Base class for chat/generation providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text response.

        Args:
            prompt: Input prompt
            **kwargs: Provider-specific parameters

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model identifier."""
        pass


class ModelProvider(ABC):
    """Base class combining embedding and chat capabilities."""

    @abstractmethod
    def get_embedding_provider(self) -> EmbeddingProvider:
        """Get embedding provider instance."""
        pass

    @abstractmethod
    def get_chat_provider(self) -> ChatProvider:
        """Get chat provider instance."""
        pass