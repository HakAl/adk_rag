"""
Document ingestion script for RAG Agent.
Supports PDF, CSV, JSONL, and Parquet files.
"""
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

try:
    import pandas as pd
    from pypdf import PdfReader
    import json
except ImportError as e:
    print(f"Missing required package: {e}")
    sys.exit(1)


def read_pdf(file_path: Path) -> List[Dict[str, Any]]:
    """Read PDF file and return documents."""
    documents = []
    reader = PdfReader(file_path)
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        documents.append({
            "content": text,
            "metadata": {"source": str(file_path), "page": page_num}
        })
    return documents


def read_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Read CSV file and return documents."""
    df = pd.read_csv(file_path)
    documents = []
    for idx, row in df.iterrows():
        documents.append({
            "content": " ".join([f"{k}: {v}" for k, v in row.items()]),
            "metadata": {"source": str(file_path), "row": idx}
        })
    return documents


def read_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Read JSONL file and return documents."""
    documents = []
    with open(file_path, 'r') as f:
        for idx, line in enumerate(f):
            data = json.loads(line)
            content = data.get("content") or data.get("text") or str(data)
            documents.append({
                "content": content,
                "metadata": {"source": str(file_path), "line": idx}
            })
    return documents


def read_parquet(file_path: Path) -> List[Dict[str, Any]]:
    """Read Parquet file and return documents."""
    df = pd.read_parquet(file_path)
    documents = []
    for idx, row in df.iterrows():
        documents.append({
            "content": " ".join([f"{k}: {v}" for k, v in row.items()]),
            "metadata": {"source": str(file_path), "row": idx}
        })
    return documents


def ingest_documents(directory: Path, file_types: List[str], overwrite: bool = False):
    """Ingest documents from directory."""
    file_readers = {
        "pdf": (read_pdf, "*.pdf"),
        "csv": (read_csv, "*.csv"),
        "jsonl": (read_jsonl, "*.jsonl"),
        "parquet": (read_parquet, "*.parquet"),
    }

    all_documents = []

    for file_type in file_types:
        if file_type not in file_readers:
            print(f"Unknown file type: {file_type}")
            continue

        reader_func, pattern = file_readers[file_type]
        files = list(directory.glob(pattern))

        print(f"Found {len(files)} {file_type} files")

        for file_path in files:
            print(f"Processing: {file_path.name}")
            try:
                docs = reader_func(file_path)
                all_documents.extend(docs)
                print(f"  Added {len(docs)} documents")
            except Exception as e:
                print(f"  Error: {e}")

    print(f"\nTotal documents ingested: {len(all_documents)}")
    return all_documents


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Ingest documents into RAG system")
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("data"),
        help="Directory containing documents"
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["pdf", "csv", "jsonl", "parquet", "all"],
        default=["all"],
        help="File types to ingest"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing vector store"
    )

    args = parser.parse_args()

    if "all" in args.types:
        file_types = ["pdf", "csv", "jsonl", "parquet"]
    else:
        file_types = args.types

    if not args.directory.exists():
        print(f"Error: Directory {args.directory} does not exist")
        sys.exit(1)

    ingest_documents(args.directory, file_types, args.overwrite)


if __name__ == "__main__":
    main()