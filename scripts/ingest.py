"""
Document ingestion script.
"""
import sys
import argparse
from pathlib import Path

from config import settings, logger
from app.core.application import RAGAgentApp


def main():
    """Main entry point for ingestion script."""
    parser = argparse.ArgumentParser(
        description="Ingest PDF documents into the RAG knowledge base"
    )
    parser.add_argument(
        '--directory',
        type=str,
        default=None,
        help=f'Directory containing PDF files (default: {settings.data_dir})'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing vector store collection'
    )
    
    args = parser.parse_args()
    
    # Determine directory
    pdf_dir = Path(args.directory) if args.directory else settings.data_dir
    
    if not pdf_dir.exists():
        print(f"\n❌ Error: Directory '{pdf_dir}' does not exist\n")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("  📚 Document Ingestion")
    print("=" * 70)
    print(f"  Source Directory: {pdf_dir}")
    print(f"  Vector Store: {settings.vector_store_dir}")
    print(f"  Overwrite Mode: {args.overwrite}")
    print(f"  Embedding Model: {settings.embedding_model}")
    print("=" * 70 + "\n")
    
    try:
        # Initialize application
        app = RAGAgentApp()
        
        # Run ingestion
        print("🔄 Starting ingestion...\n")
        num_docs, num_chunks, filenames = app.ingest_documents(
            pdf_directory=pdf_dir,
            overwrite=args.overwrite
        )
        
        # Print summary
        print("\n" + "=" * 70)
        print("  ✅ Ingestion Complete!")
        print("=" * 70)
        print(f"  Documents Processed: {num_docs}")
        print(f"  Text Chunks Created: {num_chunks}")
        print(f"\n  Files:")
        for filename in filenames:
            print(f"    • {filename}")
        print("=" * 70 + "\n")
        
        # Show stats
        stats = app.get_stats()
        vs_stats = stats['vector_store']
        print(f"  📊 Total chunks in vector store: {vs_stats['count']}")
        print(f"  🎯 Ready for queries!\n")
        
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        print(f"\n❌ Error during ingestion: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
