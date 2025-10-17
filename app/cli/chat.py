"""
Command-line interface for the RAG Agent.
"""
import asyncio
import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
import httpx

from config import settings, logger
from app.api.client import APIClient


class CLI:
    """Interactive command-line interface."""

    def __init__(self, api_client: APIClient):
        """
        Initialize CLI.

        Args:
            api_client: APIClient instance
        """
        self.api_client = api_client
        self.user_id = "cli_user"
        self.session_id: Optional[str] = None
        self.prompt_session = PromptSession(history=InMemoryHistory())

    def print_banner(self, stats: dict):
        """Print welcome banner."""
        print("\n" + "=" * 70)
        print(f"  {settings.app_name} v{settings.version}")
        print("=" * 70)
        print(f"  Environment: {settings.environment}")
        print(f"  API URL: {settings.api_base_url}")
        print(f"  Chat Model: {stats['models']['chat']}")
        print(f"  Embedding Model: {stats['models']['embedding']}")
        print("=" * 70)

        # Show vector store stats
        vs_stats = stats['vector_store']
        print(f"\n  📚 Knowledge Base Status: {vs_stats['status']}")
        if vs_stats['status'] == 'ready':
            print(f"  📊 Documents in store: {vs_stats['count']} chunks")
        else:
            print("  ⚠️  No documents loaded. Run ingestion first!")
        print("\n" + "=" * 70)
        print("  Type 'exit' or 'quit' to end the conversation")
        print("  Type 'stats' to see current statistics")
        print("  Type 'new' to start a new conversation")
        print("=" * 70 + "\n")

    async def run(self):
        """Run the interactive CLI."""
        try:
            # Check API health
            health = await self.api_client.health_check()
            logger.info(f"Connected to API v{health['version']}")

            # Get initial stats
            stats = await self.api_client.get_stats()
            self.print_banner(stats)

            # Create initial session
            self.session_id = await self.api_client.create_session(self.user_id)
            logger.info(f"Session created: {self.session_id}")

        except httpx.HTTPError as e:
            print(f"\n❌ Failed to connect to API at {settings.api_base_url}")
            print(f"   Error: {e}")
            print(f"\n   Make sure the FastAPI server is running:")
            print(f"   uvicorn main:app --reload\n")
            return

        while True:
            try:
                # Get user input with prompt_toolkit
                user_input = await self.prompt_session.prompt_async("\n💬 You: ")
                user_input = user_input.strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break

                if user_input.lower() == 'stats':
                    await self._print_stats()
                    continue

                if user_input.lower() == 'new':
                    self.session_id = await self.api_client.create_session(self.user_id)
                    print(f"\n✅ New conversation started (Session: {self.session_id[:8]}...)")
                    continue

                # Get response from agent via API
                print("\n🤖 Assistant: ", end="", flush=True)
                print("🔄 Processing", end="", flush=True)

                try:
                    response = await self.api_client.chat(
                        message=user_input,
                        user_id=self.user_id,
                        session_id=self.session_id
                    )
                    # Clear the "Processing..." line
                    print("\r🤖 Assistant: " + " " * 20 + "\r🤖 Assistant: ", end="", flush=True)
                    print(response)
                except httpx.TimeoutException:
                    print("\n⏱️  Request timed out. The agent might be processing a complex query.")
                    print("   Try increasing the timeout in settings or simplifying your question.")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except EOFError:
                print("\n\n👋 Goodbye!\n")
                break
            except httpx.HTTPError as e:
                logger.error(f"API error: {e}")
                print(f"\n❌ API Error: {e}")
            except Exception as e:
                logger.error(f"Error in CLI: {e}")
                print(f"\n❌ Error: {e}")

    async def _print_stats(self):
        """Print application statistics."""
        try:
            stats = await self.api_client.get_stats()
            print("\n" + "=" * 70)
            print("  📊 Application Statistics")
            print("=" * 70)
            print(f"  App: {stats['app_name']} v{stats['version']}")
            print(f"  Environment: {stats['environment']}")
            print(f"\n  Vector Store:")
            vs = stats['vector_store']
            print(f"    Status: {vs['status']}")
            print(f"    Collection: {vs['collection']}")
            if vs['status'] == 'ready':
                print(f"    Chunks: {vs['count']}")

            # Show available providers
            providers = stats.get('providers', {})
            print(f"\n  Available Providers:")
            print(f"    Local (Ollama): {'✅' if providers.get('local') else '❌'}")
            print(f"    Anthropic (Claude): {'✅' if providers.get('anthropic') else '❌'}")
            print(f"    Google (Gemini): {'✅' if providers.get('google') else '❌'}")

            print(f"\n  Models:")
            print(f"    Embedding: {stats['models']['embedding']}")
            print(f"    Chat: {stats['models']['chat']}")
            print("=" * 70)
        except httpx.HTTPError as e:
            print(f"\n❌ Failed to get stats: {e}")


async def main():
    """Main entry point for CLI."""
    # Use longer timeout for agent processing (default 30s is too short)
    # Agent queries can take 1-3 minutes with local LLMs and RAG
    api_client = APIClient(timeout=180)  # 3 minutes

    try:
        # Run CLI
        cli = CLI(api_client)
        await cli.run()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}\n")
        sys.exit(1)
    finally:
        await api_client.close()


if __name__ == "__main__":
    asyncio.run(main())