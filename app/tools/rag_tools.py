"""
RAG query tools for ADK agents.

These functions create tool closures that capture service instances,
which is required by the ADK framework's tool calling mechanism.
"""
from typing import List, Callable, Optional

from config import logger
from app.services.rag import RAGService
from app.services.rag_anthropic import RAGAnthropicService
from app.services.rag_google import RAGGoogleService


def create_rag_query_tool(rag_service: RAGService) -> Callable[[str], str]:
    """
    Create a RAG query tool that uses local models.

    Args:
        rag_service: RAGService instance (Ollama/llama.cpp)

    Returns:
        Callable tool function
    """
    def rag_query(query: str) -> str:
        """
        Query the local knowledge base using RAG.

        Args:
            query: User's question

        Returns:
            Answer with citations
        """
        logger.debug(f"[Tool] rag_query (local) called: '{query}'")
        answer, _ = rag_service.query(query)
        return answer

    return rag_query


def create_rag_anthropic_tool(rag_anthropic_service: RAGAnthropicService) -> Callable[[str], str]:
    """
    Create a RAG query tool that uses Anthropic Claude.

    Args:
        rag_anthropic_service: RAGAnthropicService instance

    Returns:
        Callable tool function
    """
    def rag_query_anthropic(query: str) -> str:
        """
        Query the knowledge base using Anthropic Claude for complex reasoning.

        Args:
            query: User's question

        Returns:
            Answer with citations
        """
        logger.debug(f"[Tool] rag_query_anthropic called: '{query}'")
        answer, _ = rag_anthropic_service.query(query)
        return answer

    return rag_query_anthropic


def create_rag_google_tool(rag_google_service: RAGGoogleService) -> Callable[[str], str]:
    """
    Create a RAG query tool that uses Google Gemini.

    Args:
        rag_google_service: RAGGoogleService instance

    Returns:
        Callable tool function
    """
    def rag_query_google(query: str) -> str:
        """
        Query the knowledge base using Google Gemini.

        Args:
            query: User's question

        Returns:
            Answer with citations
        """
        logger.debug(f"[Tool] rag_query_google called: '{query}'")
        answer, _ = rag_google_service.query(query)
        return answer

    return rag_query_google


def create_rag_tools(
    rag_service: RAGService,
    rag_anthropic_service: Optional[RAGAnthropicService] = None,
    rag_google_service: Optional[RAGGoogleService] = None
) -> List[Callable]:
    """
    Create all available RAG tools based on provided services.

    Args:
        rag_service: Required local RAG service
        rag_anthropic_service: Optional Anthropic RAG service
        rag_google_service: Optional Google RAG service

    Returns:
        List of tool functions
    """
    tools = [create_rag_query_tool(rag_service)]

    if rag_anthropic_service:
        tools.append(create_rag_anthropic_tool(rag_anthropic_service))

    if rag_google_service:
        tools.append(create_rag_google_tool(rag_google_service))

    return tools