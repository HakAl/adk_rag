"""
HTTP client for interacting with RAG Agent API.
"""
import httpx
from typing import Dict, Any

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
        Send a chat message and get response.

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
            "/chat",
            json={
                "message": message,
                "user_id": user_id,
                "session_id": session_id
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["response"]