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
        print(f"  Provider: {stats.get('provider_type', 'unknown')}")

        # Show models based on what's available
        if stats.get('chat_model'):
            print(f"  Chat Model: {stats['chat_model']}")
        if stats.get('embedding_model'):
            print(f"  Embedding Model: {stats['embedding_model']}")

        # Show router status
        if stats.get('router_enabled'):
            router_model = stats.get('router_model', 'unknown')
            print(f"  🎯 Router: Enabled ({router_model})")
        else:
            print(f"  🎯 Router: Disabled")

        print("=" * 70)

        # Show vector store stats
        doc_count = stats.get('document_count', 0)
        collection = stats.get('vector_store_collection', 'unknown')

        print(f"\n  📚 Knowledge Base: {collection}")
        if doc_count > 0:
            print(f"  📊 Documents in store: {doc_count} chunks")
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
            print(f"   uvicorn app.api.main:app --reload\n")
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
                    result = await self.api_client.chat(
                        message=user_input,
                        user_id=self.user_id,
                        session_id=self.session_id
                    )

                    # Clear the "Processing..." line
                    print("\r🤖 Assistant: " + " " * 20 + "\r🤖 Assistant: ", end="", flush=True)

                    # Handle dict response (with routing info) or string response (legacy)
                    if isinstance(result, dict):
                        response_text = result.get('response', str(result))

                        # Show routing info if present and in debug mode
                        if settings.debug and result.get('routing_info'):
                            routing = result['routing_info']
                            print(f"[🎯 {routing['agent']} | confidence: {routing['confidence']:.2f}]")

                        print(response_text)
                    else:
                        # Legacy string response
                        print(result)

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
            print(f"  Version: {settings.version}")
            print(f"  Environment: {settings.environment}")

            print(f"\n  Provider Configuration:")
            print(f"    Type: {stats.get('provider_type', 'unknown')}")
            if stats.get('chat_model'):
                print(f"    Chat Model: {stats['chat_model']}")
            if stats.get('embedding_model'):
                print(f"    Embedding Model: {stats['embedding_model']}")

            print(f"\n  Router:")
            if stats.get('router_enabled'):
                print(f"    Status: ✅ Enabled")
                print(f"    Model: {stats.get('router_model', 'unknown')}")
            else:
                print(f"    Status: ❌ Disabled")

            print(f"\n  Vector Store:")
            print(f"    Collection: {stats.get('vector_store_collection', 'unknown')}")
            doc_count = stats.get('document_count', 0)
            if doc_count > 0:
                print(f"    Document Chunks: {doc_count}")
            else:
                print(f"    Document Chunks: 0 (empty)")

            print("=" * 70)
        except httpx.HTTPError as e:
            print(f"\n❌ Failed to get stats: {e}")
        except Exception as e:
            logger.error(f"Error printing stats: {e}")
            print(f"\n❌ Error displaying stats: {e}")


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
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await api_client.close()


if __name__ == "__main__":
    asyncio.run(main())