"""
Document ingestion script for RAG Agent.
Supports PDF, CSV, JSONL, and Parquet files with optimizations.
"""
import argparse
import sys
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Iterator, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

try:
    import pandas as pd
    from pypdf import PdfReader
except ImportError as e:
    print(f"Missing required package: {e}")
    sys.exit(1)

# File hash cache for skip already-ingested files
CACHE_FILE = Path(".ingest_cache.json")


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file for change detection."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_cache() -> Dict[str, str]:
    """Load file hash cache."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache: Dict[str, str]):
    """Save file hash cache."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def should_process_file(file_path: Path, cache: Dict[str, str]) -> bool:
    """Check if file needs processing based on hash."""
    file_key = str(file_path)
    current_hash = compute_file_hash(file_path)

    if file_key in cache and cache[file_key] == current_hash:
        return False

    cache[file_key] = current_hash
    return True


def read_pdf_lazy(file_path: Path, chunk_size: int = 10) -> Iterator[List[Dict[str, Any]]]:
    """Read PDF file lazily in chunks to optimize memory."""
    reader = PdfReader(file_path)
    chunk = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        chunk.append({
            "content": text,
            "metadata": {"source": str(file_path), "page": page_num}
        })

        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []

    if chunk:
        yield chunk


def read_pdf(file_path: Path) -> List[Dict[str, Any]]:
    """Read PDF file and return documents."""
    documents = []
    for chunk in read_pdf_lazy(file_path):
        documents.extend(chunk)
    return documents


def read_csv_lazy(file_path: Path, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
    """Read CSV file lazily in chunks to optimize memory."""
    for chunk_df in pd.read_csv(file_path, chunksize=chunk_size):
        chunk = []
        for idx, row in chunk_df.iterrows():
            chunk.append({
                "content": " ".join([f"{k}: {v}" for k, v in row.items()]),
                "metadata": {"source": str(file_path), "row": idx}
            })
        yield chunk


def read_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Read CSV file and return documents."""
    documents = []
    for chunk in read_csv_lazy(file_path):
        documents.extend(chunk)
    return documents


def read_jsonl_lazy(file_path: Path, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
    """Read JSONL file lazily in chunks to optimize memory."""
    chunk = []
    with open(file_path, 'r') as f:
        for idx, line in enumerate(f):
            data = json.loads(line)
            content = data.get("content") or data.get("text") or str(data)
            chunk.append({
                "content": content,
                "metadata": {"source": str(file_path), "line": idx}
            })

            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []

    if chunk:
        yield chunk


def read_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Read JSONL file and return documents."""
    documents = []
    for chunk in read_jsonl_lazy(file_path):
        documents.extend(chunk)
    return documents


def read_parquet_lazy(file_path: Path, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
    """Read Parquet file lazily in chunks to optimize memory."""
    # Read in batches using pandas
    parquet_file = pd.read_parquet(file_path)

    for start_idx in range(0, len(parquet_file), chunk_size):
        chunk_df = parquet_file.iloc[start_idx:start_idx + chunk_size]
        chunk = []
        for idx, row in chunk_df.iterrows():
            chunk.append({
                "content": " ".join([f"{k}: {v}" for k, v in row.items()]),
                "metadata": {"source": str(file_path), "row": idx}
            })
        yield chunk


def read_parquet(file_path: Path) -> List[Dict[str, Any]]:
    """Read Parquet file and return documents."""
    documents = []
    for chunk in read_parquet_lazy(file_path):
        documents.extend(chunk)
    return documents


def process_single_file(file_path: Path, reader_func) -> Tuple[Path, List[Dict[str, Any]], str]:
    """Process a single file and return results."""
    try:
        docs = reader_func(file_path)
        return file_path, docs, None
    except Exception as e:
        return file_path, [], str(e)


def ingest_documents_parallel(
        directory: Path,
        file_types: List[str],
        overwrite: bool = False,
        max_workers: int = 4,
        skip_cached: bool = True
) -> List[Dict[str, Any]]:
    """Ingest documents from directory with parallel processing."""
    file_readers = {
        "pdf": (read_pdf, "*.pdf"),
        "csv": (read_csv, "*.csv"),
        "jsonl": (read_jsonl, "*.jsonl"),
        "parquet": (read_parquet, "*.parquet"),
    }

    # Load cache
    cache = load_cache() if skip_cached else {}
    if overwrite:
        cache = {}

    # Collect all files to process
    files_to_process = []
    for file_type in file_types:
        if file_type not in file_readers:
            print(f"Unknown file type: {file_type}")
            continue

        reader_func, pattern = file_readers[file_type]
        files = list(directory.glob(pattern))

        for file_path in files:
            if skip_cached and not should_process_file(file_path, cache):
                print(f"Skipping (cached): {file_path.name}")
                continue
            files_to_process.append((file_path, reader_func))

    print(f"Processing {len(files_to_process)} files...")

    # Process files in parallel
    all_documents = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_single_file, file_path, reader_func): file_path
            for file_path, reader_func in files_to_process
        }

        # Collect results as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                path, docs, error = future.result()
                if error:
                    print(f"Error processing {path.name}: {error}")
                else:
                    all_documents.extend(docs)
                    print(f"Processed {path.name}: {len(docs)} documents")
            except Exception as e:
                print(f"Error processing {file_path.name}: {e}")

    # Save cache
    if skip_cached:
        save_cache(cache)

    print(f"\nTotal documents ingested: {len(all_documents)}")
    return all_documents


def ingest_documents_batch(
        directory: Path,
        file_types: List[str],
        overwrite: bool = False,
        batch_size: int = 100
) -> Iterator[List[Dict[str, Any]]]:
    """Ingest documents in batches for memory-efficient processing."""
    file_readers = {
        "pdf": (read_pdf_lazy, "*.pdf"),
        "csv": (read_csv_lazy, "*.csv"),
        "jsonl": (read_jsonl_lazy, "*.jsonl"),
        "parquet": (read_parquet_lazy, "*.parquet"),
    }

    # Load cache
    cache = load_cache()
    if overwrite:
        cache = {}

    batch = []
    total_docs = 0

    for file_type in file_types:
        if file_type not in file_readers:
            print(f"Unknown file type: {file_type}")
            continue

        reader_func, pattern = file_readers[file_type]
        files = list(directory.glob(pattern))

        print(f"Found {len(files)} {file_type} files")

        for file_path in files:
            if not should_process_file(file_path, cache):
                print(f"Skipping (cached): {file_path.name}")
                continue

            print(f"Processing: {file_path.name}")
            try:
                for chunk in reader_func(file_path):
                    batch.extend(chunk)
                    total_docs += len(chunk)

                    # Yield batch when it reaches batch_size
                    while len(batch) >= batch_size:
                        yield batch[:batch_size]
                        batch = batch[batch_size:]

            except Exception as e:
                print(f"  Error: {e}")

    # Yield remaining documents
    if batch:
        yield batch

    # Save cache
    save_cache(cache)
    print(f"\nTotal documents ingested: {total_docs}")


def ingest_documents(directory: Path, file_types: List[str], overwrite: bool = False):
    """Ingest documents from directory (legacy method for compatibility)."""
    return ingest_documents_parallel(directory, file_types, overwrite)


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
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers"
    )
    parser.add_argument(
        "--batch-mode",
        action="store_true",
        help="Use batch processing mode (memory efficient)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for batch mode"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable file caching (process all files)"
    )

    args = parser.parse_args()

    if "all" in args.types:
        file_types = ["pdf", "csv", "jsonl", "parquet"]
    else:
        file_types = args.types

    if not args.directory.exists():
        print(f"Error: Directory {args.directory} does not exist")
        sys.exit(1)

    if args.batch_mode:
        # Batch processing mode
        for batch in ingest_documents_batch(
                args.directory,
                file_types,
                args.overwrite,
                args.batch_size
        ):
            # In real implementation, this would send batch to vector store
            pass
    else:
        # Parallel processing mode
        ingest_documents_parallel(
            args.directory,
            file_types,
            args.overwrite,
            args.workers,
            not args.no_cache
        )


if __name__ == "__main__":
    main()