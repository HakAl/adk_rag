"""
Main entry point for the RAG Agent application.
"""
import asyncio
import sys

from app.cli.chat import main as cli_main


if __name__ == "__main__":
    try:
        asyncio.run(cli_main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}\n")
        sys.exit(1)
