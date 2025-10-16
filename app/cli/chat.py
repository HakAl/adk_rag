"""
Command-line interface for the RAG Agent.
"""
import asyncio
import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from config import settings, logger
from app.core.application import RAGAgentApp


class CLI:
    """Interactive command-line interface."""

    def __init__(self, app: RAGAgentApp):
        """
        Initialize CLI.

        Args:
            app: RAGAgentApp instance
        """
        self.app = app
        self.user_id = "cli_user"
        self.session_id: Optional[str] = None
        self.prompt_session = PromptSession(history=InMemoryHistory())

    def print_banner(self):
        """Print welcome banner."""
        print("\n" + "=" * 70)
        print(f"  {settings.app_name} v{settings.version}")
        print("=" * 70)
        print(f"  Environment: {settings.environment}")
        print(f"  Chat Model: {settings.chat_model}")
        print(f"  Embedding Model: {settings.embedding_model}")
        print("=" * 70)

        # Show vector store stats
        stats = self.app.get_stats()
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
        self.print_banner()

        # Create initial session
        self.session_id = await self.app.create_session(self.user_id)
        logger.info(f"Session created: {self.session_id}")

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
                    self._print_stats()
                    continue

                if user_input.lower() == 'new':
                    self.session_id = await self.app.create_session(self.user_id)
                    print(f"\n✅ New conversation started (Session: {self.session_id[:8]}...)")
                    continue

                # Get response from agent
                print("\n🤖 Assistant: ", end="", flush=True)
                response = await self.app.chat(
                    message=user_input,
                    user_id=self.user_id,
                    session_id=self.session_id
                )
                print(response)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except EOFError:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                logger.error(f"Error in CLI: {e}")
                print(f"\n❌ Error: {e}")

    def _print_stats(self):
        """Print application statistics."""
        stats = self.app.get_stats()
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
        print(f"\n  Models:")
        print(f"    Embedding: {stats['models']['embedding']}")
        print(f"    Chat: {stats['models']['chat']}")
        print("=" * 70)


async def main():
    """Main entry point for CLI."""
    try:
        # Initialize application
        app = RAGAgentApp()

        # Run CLI
        cli = CLI(app)
        await cli.run()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())