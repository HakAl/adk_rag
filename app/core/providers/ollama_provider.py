"""
llama.cpp provider implementation.
"""
from pathlib import Path
from typing import Optional
from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import LlamaCppEmbeddings
from .base import ModelProvider, EmbeddingProvider, ChatProvider


class LlamaCppEmbeddingProvider(EmbeddingProvider):
    """llama.cpp embedding provider."""

    def __init__(
            self,
            model_path: str,
            n_ctx: int = 2048,
            n_batch: int = 512,
            n_threads: Optional[int] = None
    ):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.n_threads = n_threads
        self._embeddings = None

    def get_embeddings(self):
        if self._embeddings is None:
            self._embeddings = LlamaCppEmbeddings(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                n_threads=self.n_threads
            )
        return self._embeddings


class LlamaCppChatProvider(ChatProvider):
    """llama.cpp chat provider."""

    def __init__(
            self,
            model_path: str,
            n_ctx: int = 2048,
            n_batch: int = 512,
            n_threads: Optional[int] = None,
            temperature: float = 0.7,
            max_tokens: int = 512,
            verbose: bool = False
    ):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.n_threads = n_threads
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = LlamaCpp(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                n_threads=self.n_threads,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                verbose=self.verbose
            )
        return self._llm

    def generate(self, prompt: str, **kwargs) -> str:
        llm = self._get_llm()

        # Override defaults with kwargs
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)

        response = llm.invoke(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.strip()

    def get_model_name(self) -> str:
        return Path(self.model_path).name


class LlamaCppProvider(ModelProvider):
    """Complete llama.cpp provider for embeddings and chat."""

    def __init__(
            self,
            embedding_model_path: str,
            chat_model_path: str,
            n_ctx: int = 2048,
            n_batch: int = 512,
            n_threads: Optional[int] = None,
            temperature: float = 0.7,
            max_tokens: int = 512,
            verbose: bool = False
    ):
        self.embedding_model_path = embedding_model_path
        self.chat_model_path = chat_model_path
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.n_threads = n_threads
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose

        self._embedding_provider = None
        self._chat_provider = None

    def get_embedding_provider(self) -> EmbeddingProvider:
        if self._embedding_provider is None:
            self._embedding_provider = LlamaCppEmbeddingProvider(
                model_path=self.embedding_model_path,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                n_threads=self.n_threads
            )
        return self._embedding_provider

    def get_chat_provider(self) -> ChatProvider:
        if self._chat_provider is None:
            self._chat_provider = LlamaCppChatProvider(
                model_path=self.chat_model_path,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                n_threads=self.n_threads,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                verbose=self.verbose
            )
        return self._chat_provider