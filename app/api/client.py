import httpx
import json
import os
from pathlib import Path
from typing import Dict, Any, AsyncGenerator, Optional

from config import settings, logger


class APIClient:
    """Client for RAG Agent API with authentication support."""

    def __init__(self, base_url: str = None, timeout: int = None):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.base_url = base_url or settings.api_base_url
        self.timeout = timeout or settings.api_timeout
        self.api_token = self._load_api_token()

        # Create client with default headers
        headers = {}
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
            logger.info("API token loaded from config")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=headers
        )

    def _load_api_token(self) -> Optional[str]:
        """
        Load API token from config file.

        Looks for ~/.ragagent/config.json with format:
        {
            "api_token": "vba_..."
        }
        """
        config_path = Path.home() / '.ragagent' / 'config.json'

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            logger.warning("CLI will not have authentication. Create config file with API token.")
            return None

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                token = config.get('api_token')

                if not token:
                    logger.warning("No api_token found in config file")
                    return None

                if not token.startswith('vba_'):
                    logger.warning("Invalid token format (should start with 'vba_')")
                    return None

                return token

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None

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
        Create a new chat session (requires authentication).

        Args:
            user_id: User identifier (ignored, uses authenticated user)

        Returns:
            Session ID

        Raises:
            httpx.HTTPError: If request fails (401 if not authenticated)
        """
        response = await self.client.post("/sessions/coordinator", json={})
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
        Send a chat message and get response via coordinator.

        Args:
            message: User message
            user_id: User identifier (ignored, uses authenticated user)
            session_id: Session identifier

        Returns:
            Assistant response

        Raises:
            httpx.HTTPError: If request fails (401 if not authenticated)
        """
        response = await self.client.post(
            "/chat/coordinator",
            json={
                "message": message,
                "session_id": session_id  # CLI sends session_id in body
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
            user_id: User identifier (ignored, uses authenticated user)
            session_id: Session identifier

        Yields:
            Event dictionaries with type and data fields

        Raises:
            httpx.HTTPError: If request fails (401 if not authenticated)
        """
        async with self.client.stream(
            "POST",
            "/chat/coordinator/stream",
            json={
                "message": message,
                "session_id": session_id  # CLI sends session_id in body
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