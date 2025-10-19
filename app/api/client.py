"""
HTTP client for interacting with RAG Agent API.
"""
import httpx
import json
from typing import Dict, Any, AsyncGenerator

from config import settings, logger


class APIClient:
    """Client for RAG Agent API."""

    def __init__(self, base_url: str = None, timeout: int = None):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.base_url = base_url or settings.api_base_url
        self.timeout = timeout or settings.api_timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, str]:
        """
        Check API health.

        Returns:
            Health status and version

        Raises:
            httpx.HTTPError: If request fails
        """
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get application statistics.

        Returns:
            Application statistics

        Raises:
            httpx.HTTPError: If request fails
        """
        response = await self.client.get("/stats")
        response.raise_for_status()
        return response.json()

    async def create_session(self, user_id: str = "api_user") -> str:
        """
        Create a new chat session.

        Args:
            user_id: User identifier

        Returns:
            Session ID

        Raises:
            httpx.HTTPError: If request fails
        """
        response = await self.client.post(
            "/sessions",
            json={"user_id": user_id}
        )
        response.raise_for_status()
        data = response.json()
        return data["session_id"]

    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> str:
        """
        Send a chat message and get response via coordinator with routing.

        Args:
            message: User message
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Assistant response

        Raises:
            httpx.HTTPError: If request fails
        """
        response = await self.client.post(
            "/chat/coordinator",
            json={
                "message": message,
                "user_id": user_id,
                "session_id": session_id
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["response"]

    async def chat_stream(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a chat message and stream the response via coordinator.

        Args:
            message: User message
            user_id: User identifier
            session_id: Session identifier

        Yields:
            Event dictionaries with type and data fields

        Raises:
            httpx.HTTPError: If request fails
        """
        async with self.client.stream(
            "POST",
            "/chat/coordinator/stream",
            json={
                "message": message,
                "user_id": user_id,
                "session_id": session_id
            }
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                # SSE format: "data: {...}\n"
                if line.startswith("data: "):
                    try:
                        data = line[6:]  # Remove "data: " prefix
                        event = json.loads(data)
                        yield event
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse SSE event: {line} - {e}")
                        continue