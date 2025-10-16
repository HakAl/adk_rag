"""
RAG service using Anthropic's Claude API.
"""
import os
from typing import List, Tuple, Optional
from anthropic import Anthropic

from config import settings, logger
from app.services.vector_store import VectorStoreService


class RAGAnthropicService:
    """Service for answering queries using RAG with Anthropic Claude."""

    def __init__(self, vector_store: VectorStoreService):
        """
        Initialize RAG Anthropic service.

        Args:
            vector_store: VectorStoreService instance
        """
        self.vector_store = vector_store
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        logger.info(f"RAGAnthropicService initialized with model: {self.model}")

    def query(
            self,
            question: str,
            k: Optional[int] = None,
            include_sources: bool = True
    ) -> Tuple[str, Optional[List[str]]]:
        """
        Answer a question using RAG with Anthropic.

        Args:
            question: User's question
            k: Number of documents to retrieve
            include_sources: Whether to include source citations

        Returns:
            Tuple of (answer, sources)
        """
        logger.info(f"[Anthropic] Processing query: '{question}'")

        # Retrieve relevant documents
        try:
            retriever = self.vector_store.get_retriever(k=k)
            results = retriever.invoke(question)
        except ValueError:
            return (
                "📚 No documents in knowledge base. Please run ingestion first.",
                None
            )
        except Exception as e:
            logger.error(f"[Anthropic] Retrieval error: {e}")
            return f"❌ Error during retrieval: {str(e)}", None

        if not results:
            return "❓ No relevant information found in the knowledge base.", None

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

        # Generate answer using Anthropic
        try:
            answer = self._generate(prompt)
            logger.info("[Anthropic] Answer generated successfully")

            if include_sources and sources:
                answer = f"{answer}\n\n📚 Sources: {', '.join(sources)}"

            return answer, sources
        except Exception as e:
            logger.error(f"[Anthropic] Generation error: {e}")
            return f"❌ Error generating answer: {str(e)}", sources

    def _build_prompt(self, question: str, contexts: List[str]) -> str:
        """Build prompt for Claude."""
        context_text = "\n\n".join([
            f"[Context {i + 1}]\n{ctx}"
            for i, ctx in enumerate(contexts)
        ])

        return f"""You are a helpful assistant. Answer the question concisely using only the provided context below. If you cannot answer based on the context, say so clearly.

Context:
{context_text}

Question: {question}

Answer:"""

    def _generate(self, prompt: str) -> str:
        """Generate answer using Anthropic Claude."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text.strip()