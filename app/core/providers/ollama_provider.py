"""
Ollama provider implementation.
"""
from typing import TYPE_CHECKING

import litellm
from .base import ModelProvider, EmbeddingProvider, ChatProvider

# Conditional import - only loaded when Ollama provider is actually used
if TYPE_CHECKING:
    from langchain_ollama import OllamaEmbeddings


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider."""

    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url
        self._embeddings = None

    def get_embeddings(self):
        if self._embeddings is None:
            # Import only when actually needed
            from langchain_ollama import OllamaEmbeddings

            self._embeddings = OllamaEmbeddings(
                model=self.model,
                base_url=self.base_url
            )
        return self._embeddings


class OllamaChatProvider(ChatProvider):
    """Ollama chat provider."""

    def __init__(self, model: str, base_url: str, debug: bool = False):
        self.model = model
        self.base_url = base_url
        self.debug = debug
        litellm.set_verbose = debug

    def generate(self, prompt: str, **kwargs) -> str:
        messages = [{"role": "user", "content": prompt}]

        response = litellm.completion(
            model=f"ollama/{self.model}",
            messages=messages,
            api_base=self.base_url,
            **kwargs
        )

        return response.choices[0].message.content.strip()

    def get_model_name(self) -> str:
        return self.model


class OllamaProvider(ModelProvider):
    """Complete Ollama provider for embeddings and chat."""

    def __init__(
        self,
        embedding_model: str,
        chat_model: str,
        base_url: str,
        debug: bool = False
    ):
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        self.base_url = base_url
        self.debug = debug

        self._embedding_provider = None
        self._chat_provider = None

    def get_embedding_provider(self) -> EmbeddingProvider:
        if self._embedding_provider is None:
            self._embedding_provider = OllamaEmbeddingProvider(
                model=self.embedding_model,
                base_url=self.base_url
            )
        return self._embedding_provider

    def get_chat_provider(self) -> ChatProvider:
        if self._chat_provider is None:
            self._chat_provider = OllamaChatProvider(
                model=self.chat_model,
                base_url=self.base_url,
                debug=self.debug
            )
        return self._chat_provider