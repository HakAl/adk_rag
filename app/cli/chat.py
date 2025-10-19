"""
Command-line interface for the RAG Agent with streaming support.
"""
import asyncio
import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.validation import Validator, ValidationError as PTValidationError
import httpx

from config import settings, logger
from app.api.client import APIClient


class MessageValidator(Validator):
    """Validator for CLI input using prompt_toolkit."""

    def __init__(self, max_length: int = 8000):
        """
        Initialize validator.

        Args:
            max_length: Maximum message length
        """
        self.max_length = max_length

    def validate(self, document):
        """
        Validate the input document.

        Args:
            document: prompt_toolkit document

        Raises:
            PTValidationError: If validation fails
        """
        text = document.text.strip()

        # Check length
        if len(text) > self.max_length:
            raise PTValidationError(
                message=f'Message too long ({len(text)}/{self.max_length} chars)',
                cursor_position=len(document.text)
            )

        # Check for null bytes
        if '\x00' in text:
            raise PTValidationError(
                message='Message contains invalid null bytes',
                cursor_position=text.index('\x00')
            )


class CLI:
    """Interactive command-line interface with streaming support."""

    def __init__(self, api_client: APIClient):
        """
        Initialize CLI.

        Args:
            api_client: APIClient instance
        """
        self.api_client = api_client
        self.user_id = "cli_user"
        self.session_id: Optional[str] = None
        self.prompt_session = PromptSession(
            history=InMemoryHistory(),
            validator=MessageValidator(),
            validate_while_typing=False  # Only validate on submit
        )

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
        print("  Type 'help' to see available commands")
        print("=" * 70 + "\n")

    def print_help(self):
        """Print help information."""
        print("\n" + "=" * 70)
        print("  Available Commands")
        print("=" * 70)
        print("  exit, quit, q     - Exit the application")
        print("  stats             - Show application statistics")
        print("  new               - Start a new conversation")
        print("  help              - Show this help message")
        print("\n  Input Limits:")
        print("  - Maximum message length: 8000 characters")
        print("  - Messages are validated for security")
        print("\n  Features:")
        print("  - 🔄 Real-time streaming responses")
        print("  - 🎯 Smart routing to specialized agents")
        print("=" * 70 + "\n")

    def validate_user_input(self, user_input: str) -> tuple[bool, Optional[str]]:
        """
        Validate user input for potential issues.

        Args:
            user_input: Raw user input

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Import here to avoid circular dependency
        try:
            from app.utils.input_sanitizer import get_sanitizer, InputSanitizationError

            try:
                # This will raise InputSanitizationError if invalid
                get_sanitizer().sanitize_message(user_input)
                return True, None
            except InputSanitizationError as e:
                return False, str(e)
        except ImportError:
            # If sanitizer not available, do basic validation
            if len(user_input) > 8000:
                return False, f"Message too long ({len(user_input)}/8000 characters)"
            if '\x00' in user_input:
                return False, "Message contains invalid characters"
            return True, None

    async def run(self):
        """Run the interactive CLI with streaming support."""
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
                # Get user input with prompt_toolkit (includes basic validation)
                user_input = await self.prompt_session.prompt_async("\n💬 You: ")
                user_input = user_input.strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break

                if user_input.lower() == 'help':
                    self.print_help()
                    continue

                if user_input.lower() == 'stats':
                    await self._print_stats()
                    continue

                if user_input.lower() == 'new':
                    self.session_id = await self.api_client.create_session(self.user_id)
                    print(f"\n✅ New conversation started (Session: {self.session_id[:8]}...)")
                    continue

                # Additional validation beyond prompt_toolkit
                is_valid, error_msg = self.validate_user_input(user_input)
                if not is_valid:
                    print(f"\n⚠️  Input Validation Error: {error_msg}")
                    print("   Please rephrase your message and try again.\n")
                    continue

                # Stream response from agent via API
                try:
                    await self._handle_streaming_response(user_input)

                except httpx.HTTPStatusError as e:
                    # Handle HTTP errors from API (including validation errors)
                    print(f"\n\n❌ Server Error: ", end="")

                    if e.response.status_code == 400:
                        # Bad request - likely validation error
                        try:
                            error_detail = e.response.json()
                            if 'error' in error_detail:
                                print(error_detail['error'])
                            elif 'detail' in error_detail:
                                print(error_detail['detail'])
                            else:
                                print("Invalid input")
                        except:
                            print("Invalid input")
                    elif e.response.status_code == 422:
                        # Unprocessable entity - Pydantic validation error
                        print("Input validation failed. Please check your message.")
                    elif e.response.status_code == 429:
                        # Rate limited
                        print("Rate limit exceeded. Please wait a moment and try again.")
                    else:
                        print(f"HTTP {e.response.status_code}: {e}")

                    logger.error(f"HTTP error: {e}")

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
                logger.error(f"Error in CLI: {e}", exc_info=True)
                print(f"\n❌ Error: {e}")

    async def _handle_streaming_response(self, user_input: str):
        """
        Handle streaming response from the API.

        Args:
            user_input: User's message
        """
        print("\n🤖 Assistant: ", end="", flush=True)

        routing_shown = False
        response_started = False

        async for event in self.api_client.chat_stream(
            message=user_input,
            user_id=self.user_id,
            session_id=self.session_id
        ):
            event_type = event.get("type")
            event_data = event.get("data", {})

            if event_type == "routing":
                # Show routing info
                agent_name = event_data.get("agent_name", "Unknown")
                confidence = event_data.get("confidence", 0.0)

                if settings.debug:
                    # In debug mode, show detailed routing
                    reasoning = event_data.get("reasoning", "")
                    print(f"[🎯 {agent_name} | confidence: {confidence:.2f}]")
                    if reasoning:
                        print(f"[💭 {reasoning}]")
                    print("\n🤖 Assistant: ", end="", flush=True)
                else:
                    # In normal mode, just show a brief indicator
                    print(f"🎯 {agent_name}...\n\n", end="", flush=True)

                routing_shown = True

            elif event_type == "content":
                # Stream content chunks as they arrive
                if not response_started:
                    response_started = True
                print(event_data, end="", flush=True)

            elif event_type == "done":
                # Response complete
                if response_started:
                    print("\n")  # Final newline after response
                else:
                    print("(No response generated)\n")

            elif event_type == "error":
                # Handle error events
                error_msg = event_data.get("message", "Unknown error")
                print(f"\n\n❌ Error: {error_msg}\n")
                break

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

            print(f"\n  Features:")
            print(f"    Streaming: ✅ Enabled")
            print(f"    Input Validation: ✅ Enabled")
            print(f"    Max Message Length: 8000 characters")
            print(f"    Rate Limiting: ✅ Enabled (server-side)")

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