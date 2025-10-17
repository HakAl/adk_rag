"""
Tests for provider abstraction layer.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.providers import (
    ProviderFactory,
    OllamaProvider,
    LlamaCppProvider,
    EmbeddingProvider,
    ChatProvider
)


class TestProviderFactory:
    """Tests for ProviderFactory."""

    def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        provider = ProviderFactory.create_provider(
            'ollama',
            embedding_model='nomic-embed-text',
            chat_model='phi3:mini',
            base_url='http://localhost:11434',
            debug=False
        )

        assert isinstance(provider, OllamaProvider)
        assert provider.embedding_model == 'nomic-embed-text'
        assert provider.chat_model == 'phi3:mini'
        assert provider.base_url == 'http://localhost:11434'

    def test_create_llamacpp_provider(self):
        """Test creating llama.cpp provider."""
        provider = ProviderFactory.create_provider(
            'llamacpp',
            embedding_model_path='/path/to/embed.gguf',
            chat_model_path='/path/to/chat.gguf',
            n_ctx=2048,
            n_batch=512
        )

        assert isinstance(provider, LlamaCppProvider)
        assert provider.embedding_model_path == '/path/to/embed.gguf'
        assert provider.chat_model_path == '/path/to/chat.gguf'
        assert provider.n_ctx == 2048

    def test_create_unsupported_provider(self):
        """Test error on unsupported provider type."""
        with pytest.raises(ValueError, match="Unsupported provider type"):
            ProviderFactory.create_provider('unsupported')

    def test_create_ollama_missing_params(self):
        """Test error when missing required Ollama params."""
        with pytest.raises(ValueError, match="Missing required parameter"):
            ProviderFactory.create_provider('ollama', embedding_model='test')

    def test_create_llamacpp_missing_params(self):
        """Test error when missing required llama.cpp params."""
        with pytest.raises(ValueError, match="Missing required parameter"):
            ProviderFactory.create_provider('llamacpp', embedding_model_path='/path')


class TestOllamaProvider:
    """Tests for OllamaProvider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = OllamaProvider(
            embedding_model='nomic-embed-text',
            chat_model='phi3:mini',
            base_url='http://localhost:11434',
            debug=True
        )

        assert provider.embedding_model == 'nomic-embed-text'
        assert provider.chat_model == 'phi3:mini'
        assert provider.debug is True

    @patch('app.core.providers.ollama_provider.OllamaEmbeddings')
    def test_get_embedding_provider(self, mock_embeddings):
        """Test getting embedding provider."""
        provider = OllamaProvider(
            embedding_model='nomic-embed-text',
            chat_model='phi3:mini',
            base_url='http://localhost:11434'
        )

        embedding_provider = provider.get_embedding_provider()
        assert isinstance(embedding_provider, EmbeddingProvider)

        # Should return same instance on second call
        embedding_provider2 = provider.get_embedding_provider()
        assert embedding_provider is embedding_provider2

    def test_get_chat_provider(self):
        """Test getting chat provider."""
        provider = OllamaProvider(
            embedding_model='nomic-embed-text',
            chat_model='phi3:mini',
            base_url='http://localhost:11434'
        )

        chat_provider = provider.get_chat_provider()
        assert isinstance(chat_provider, ChatProvider)

        # Should return same instance on second call
        chat_provider2 = provider.get_chat_provider()
        assert chat_provider is chat_provider2

    @patch('app.core.providers.ollama_provider.litellm.completion')
    def test_chat_generate(self, mock_completion):
        """Test chat generation."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_completion.return_value = mock_response

        provider = OllamaProvider(
            embedding_model='nomic-embed-text',
            chat_model='phi3:mini',
            base_url='http://localhost:11434'
        )

        chat_provider = provider.get_chat_provider()
        response = chat_provider.generate("Test prompt")

        assert response == "Test response"
        mock_completion.assert_called_once()

    def test_chat_get_model_name(self):
        """Test getting model name."""
        provider = OllamaProvider(
            embedding_model='nomic-embed-text',
            chat_model='phi3:mini',
            base_url='http://localhost:11434'
        )

        chat_provider = provider.get_chat_provider()
        assert chat_provider.get_model_name() == 'phi3:mini'


class TestLlamaCppProvider:
    """Tests for LlamaCppProvider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = LlamaCppProvider(
            embedding_model_path='/path/to/embed.gguf',
            chat_model_path='/path/to/chat.gguf',
            n_ctx=2048,
            n_batch=512,
            temperature=0.7,
            verbose=True
        )

        assert provider.embedding_model_path == '/path/to/embed.gguf'
        assert provider.chat_model_path == '/path/to/chat.gguf'
        assert provider.n_ctx == 2048
        assert provider.temperature == 0.7
        assert provider.verbose is True

    def test_get_embedding_provider(self):
        """Test getting embedding provider."""
        provider = LlamaCppProvider(
            embedding_model_path='/path/to/embed.gguf',
            chat_model_path='/path/to/chat.gguf'
        )

        embedding_provider = provider.get_embedding_provider()
        assert isinstance(embedding_provider, EmbeddingProvider)

        # Should return same instance on second call
        embedding_provider2 = provider.get_embedding_provider()
        assert embedding_provider is embedding_provider2

    def test_get_chat_provider(self):
        """Test getting chat provider."""
        provider = LlamaCppProvider(
            embedding_model_path='/path/to/embed.gguf',
            chat_model_path='/path/to/chat.gguf'
        )

        chat_provider = provider.get_chat_provider()
        assert isinstance(chat_provider, ChatProvider)

        # Should return same instance on second call
        chat_provider2 = provider.get_chat_provider()
        assert chat_provider is chat_provider2

    @patch('app.core.providers.llamacpp_provider.LlamaCpp')
    def test_chat_generate(self, mock_llamacpp):
        """Test chat generation."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = "Test response"
        mock_llamacpp.return_value = mock_llm

        provider = LlamaCppProvider(
            embedding_model_path='/path/to/embed.gguf',
            chat_model_path='/path/to/chat.gguf',
            temperature=0.7,
            max_tokens=512
        )

        chat_provider = provider.get_chat_provider()
        response = chat_provider.generate("Test prompt")

        assert response == "Test response"
        mock_llm.invoke.assert_called_once()

    def test_chat_get_model_name(self):
        """Test getting model name."""
        provider = LlamaCppProvider(
            embedding_model_path='/path/to/embed.gguf',
            chat_model_path='/models/test-model.gguf'
        )

        chat_provider = provider.get_chat_provider()
        assert chat_provider.get_model_name() == 'test-model.gguf'

    @patch('app.core.providers.llamacpp_provider.LlamaCpp')
    def test_chat_generate_with_kwargs(self, mock_llamacpp):
        """Test chat generation with custom parameters."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = "Test response"
        mock_llamacpp.return_value = mock_llm

        provider = LlamaCppProvider(
            embedding_model_path='/path/to/embed.gguf',
            chat_model_path='/path/to/chat.gguf',
            temperature=0.7,
            max_tokens=512
        )

        chat_provider = provider.get_chat_provider()
        response = chat_provider.generate(
            "Test prompt",
            temperature=0.9,
            max_tokens=1024
        )

        assert response == "Test response"
        # Verify kwargs were passed
        call_kwargs = mock_llm.invoke.call_args[1]
        assert call_kwargs['temperature'] == 0.9
        assert call_kwargs['max_tokens'] == 1024


class TestProviderInterfaces:
    """Test that providers implement required interfaces."""

    def test_ollama_implements_embedding_provider(self):
        """Test Ollama embedding provider implements interface."""
        provider = OllamaProvider(
            embedding_model='test',
            chat_model='test',
            base_url='http://localhost:11434'
        )

        embedding_provider = provider.get_embedding_provider()
        assert hasattr(embedding_provider, 'get_embeddings')
        assert callable(embedding_provider.get_embeddings)

    def test_ollama_implements_chat_provider(self):
        """Test Ollama chat provider implements interface."""
        provider = OllamaProvider(
            embedding_model='test',
            chat_model='test',
            base_url='http://localhost:11434'
        )

        chat_provider = provider.get_chat_provider()
        assert hasattr(chat_provider, 'generate')
        assert hasattr(chat_provider, 'get_model_name')
        assert callable(chat_provider.generate)
        assert callable(chat_provider.get_model_name)

    def test_llamacpp_implements_embedding_provider(self):
        """Test llama.cpp embedding provider implements interface."""
        provider = LlamaCppProvider(
            embedding_model_path='/path/to/embed.gguf',
            chat_model_path='/path/to/chat.gguf'
        )

        embedding_provider = provider.get_embedding_provider()
        assert hasattr(embedding_provider, 'get_embeddings')
        assert callable(embedding_provider.get_embeddings)

    def test_llamacpp_implements_chat_provider(self):
        """Test llama.cpp chat provider implements interface."""
        provider = LlamaCppProvider(
            embedding_model_path='/path/to/embed.gguf',
            chat_model_path='/path/to/chat.gguf'
        )

        chat_provider = provider.get_chat_provider()
        assert hasattr(chat_provider, 'generate')
        assert hasattr(chat_provider, 'get_model_name')
        assert callable(chat_provider.generate)
        assert callable(chat_provider.get_model_name)