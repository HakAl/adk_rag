"""
RAG (Retrieval-Augmented Generation) service.
"""
import os
from typing import List, Tuple, Optional

from config import settings, logger
from app.services.vector_store import VectorStoreService
from app.core.providers import ProviderFactory


class RAGService:
    """Service for answering queries using RAG."""

    def __init__(self, vector_store: Optional[VectorStoreService], provider_type: Optional[str] = None):
        """
        Initialize RAG service.

        Args:
            vector_store: VectorStoreService instance (can be None in cloud mode)
            provider_type: Provider type override (defaults to settings.provider_type)
        """
        self.vector_store = vector_store
        provider_type = provider_type or settings.provider_type

        # Cloud mode - no local RAG
        if provider_type == 'cloud':
            logger.info("Cloud mode: local RAG disabled")
            self.chat_provider = None
            return

        # Validate vector store for local modes
        if vector_store is None:
            raise ValueError("Vector store required for local RAG service")

        # Create provider based on type
        if provider_type == 'ollama':
            provider = ProviderFactory.create_provider(
                'ollama',
                embedding_model=settings.embedding_model,
                chat_model=settings.chat_model,
                base_url=settings.ollama_base_url,
                debug=settings.debug
            )
        elif provider_type == 'llamacpp':
            if not settings.llamacpp_chat_model_path:
                raise ValueError("LLAMACPP_CHAT_MODEL_PATH not configured")

            provider = ProviderFactory.create_provider(
                'llamacpp',
                embedding_model_path=settings.llamacpp_embedding_model_path or settings.llamacpp_chat_model_path,
                chat_model_path=settings.llamacpp_chat_model_path,
                n_ctx=settings.llamacpp_n_ctx,
                n_batch=settings.llamacpp_n_batch,
                n_threads=settings.llamacpp_n_threads,
                temperature=settings.llamacpp_temperature,
                max_tokens=settings.llamacpp_max_tokens,
                verbose=settings.debug
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        self.chat_provider = provider.get_chat_provider()

    def query(
        self,
        question: str,
        k: Optional[int] = None,
        include_sources: bool = True
    ) -> Tuple[str, Optional[List[str]]]:
        """
        Answer a question using RAG.

        Args:
            question: User's question
            k: Number of documents to retrieve
            include_sources: Whether to include source citations

        Returns:
            Tuple of (answer, sources)
        """
        if self.chat_provider is None:
            return "❌ Local RAG not available in cloud mode", None

        if self.vector_store is None:
            return "❌ Vector store not initialized", None

        logger.info(f"Processing query: '{question}'")

        # Retrieve relevant documents
        try:
            retriever = self.vector_store.get_retriever(k=k)
            results = retriever.invoke(question)
        except ValueError as e:
            return (
                "📚 No documents in knowledge base. Please run ingestion first.",
                None
            )
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return f"❌ Error during retrieval: {str(e)}", None

        if not results:
            return "ℹ️ No relevant information found in the knowledge base.", None

        # Extract context and sources
        contexts = [doc.page_content for doc in results]
        sources = None
        if include_sources:
            sources = list(set([
                os.path.basename(doc.metadata.get('source', 'Unknown'))
                for doc in results
            ]))

        # Build prompt
        prompt = self._build_prompt(question, contexts)

        # Generate answer
        try:
            answer = self.chat_provider.generate(prompt)
            logger.info("Answer generated successfully")

            if include_sources and sources:
                answer = f"{answer}\n\n📚 Sources: {', '.join(sources)}"

            return answer, sources
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"❌ Error generating answer: {str(e)}", sources

    def _build_prompt(self, question: str, contexts: List[str]) -> str:
        """Build prompt for the LLM."""
        context_text = "\n\n".join([
            f"[Context {i+1}]\n{ctx}"
            for i, ctx in enumerate(contexts)
        ])

        return f"""You are a helpful assistant. Answer the question concisely using only the provided context below. If you cannot answer based on the context, say so clearly.

Context:
{context_text}

Question: {question}

Answer:"""