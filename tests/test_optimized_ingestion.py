"""
Unit tests for optimized document ingestion features.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import hashlib
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from ingest import (
    compute_file_hash,
    load_cache,
    save_cache,
    should_process_file,
    read_pdf_lazy,
    read_csv_lazy,
    read_jsonl_lazy,
    read_parquet_lazy,
    process_single_file,
    ingest_documents_parallel,
    ingest_documents_batch,
    read_csv,
    read_parquet,
)


class TestFileHashing:
    """Tests for file hash-based caching."""

    def test_compute_file_hash(self, tmp_path):
        """Test computing file hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        hash1 = compute_file_hash(test_file)
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 produces 64 hex chars

        # Same content should produce same hash
        hash2 = compute_file_hash(test_file)
        assert hash1 == hash2

        # Different content should produce different hash
        test_file.write_text("Different content")
        hash3 = compute_file_hash(test_file)
        assert hash1 != hash3

    def test_should_process_file_new(self, tmp_path):
        """Test that new files should be processed."""
        test_file = tmp_path / "new.txt"
        test_file.write_text("New file")

        cache = {}
        assert should_process_file(test_file, cache) is True
        assert str(test_file) in cache

    def test_should_process_file_unchanged(self, tmp_path):
        """Test that unchanged files should be skipped."""
        test_file = tmp_path / "unchanged.txt"
        test_file.write_text("Unchanged")

        cache = {}
        # First time - should process
        assert should_process_file(test_file, cache) is True

        # Second time - should skip (unchanged)
        assert should_process_file(test_file, cache) is False

    def test_should_process_file_modified(self, tmp_path):
        """Test that modified files should be processed."""
        test_file = tmp_path / "modified.txt"
        test_file.write_text("Original")

        cache = {}
        should_process_file(test_file, cache)

        # Modify file
        test_file.write_text("Modified")

        # Should process again
        assert should_process_file(test_file, cache) is True

    def test_cache_persistence(self, tmp_path):
        """Test cache save and load."""
        cache = {
            "file1.txt": "hash1",
            "file2.txt": "hash2"
        }

        # Change to tmp_path for cache file
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            save_cache(cache)
            loaded_cache = load_cache()
            assert loaded_cache == cache
        finally:
            os.chdir(original_cwd)


class TestLazyReading:
    """Tests for lazy/chunked file reading."""

    def test_csv_lazy_reading(self, tmp_path):
        """Test lazy CSV reading in chunks."""
        df = pd.DataFrame({
            "id": range(100),
            "text": [f"Document {i}" for i in range(100)]
        })
        csv_file = tmp_path / "large.csv"
        df.to_csv(csv_file, index=False)

        chunks = list(read_csv_lazy(csv_file, chunk_size=25))

        # Should have 4 chunks of 25 each
        assert len(chunks) == 4
        assert all(len(chunk) == 25 for chunk in chunks)

        # Verify content
        all_docs = [doc for chunk in chunks for doc in chunk]
        assert len(all_docs) == 100

    def test_jsonl_lazy_reading(self, tmp_path):
        """Test lazy JSONL reading in chunks."""
        jsonl_file = tmp_path / "large.jsonl"
        with open(jsonl_file, 'w') as f:
            for i in range(50):
                f.write(json.dumps({"content": f"Document {i}"}) + "\n")

        chunks = list(read_jsonl_lazy(jsonl_file, chunk_size=10))

        # Should have 5 chunks of 10 each
        assert len(chunks) == 5
        assert all(len(chunk) == 10 for chunk in chunks)

    def test_parquet_lazy_reading(self, tmp_path):
        """Test lazy Parquet reading in chunks."""
        df = pd.DataFrame({
            "id": range(75),
            "content": [f"Doc {i}" for i in range(75)]
        })
        parquet_file = tmp_path / "large.parquet"
        df.to_parquet(parquet_file)

        chunks = list(read_parquet_lazy(parquet_file, chunk_size=20))

        # Should have 4 chunks (20, 20, 20, 15)
        assert len(chunks) == 4
        assert len(chunks[0]) == 20
        assert len(chunks[-1]) == 15

    def test_lazy_reading_empty_file(self, tmp_path):
        """Test lazy reading with empty files."""
        df = pd.DataFrame()
        csv_file = tmp_path / "empty.csv"
        df.to_csv(csv_file, index=False)

        chunks = list(read_csv_lazy(csv_file))
        assert len(chunks) == 0


class TestParallelProcessing:
    """Tests for parallel file processing."""

    def test_process_single_file_success(self, tmp_path):
        """Test processing a single file successfully."""
        df = pd.DataFrame({"id": [1, 2], "text": ["A", "B"]})
        csv_file = tmp_path / "test.csv"
        df.to_csv(csv_file, index=False)

        path, docs, error = process_single_file(csv_file, read_csv)

        assert path == csv_file
        assert len(docs) == 2
        assert error is None

    def test_process_single_file_error(self, tmp_path):
        """Test error handling in single file processing."""
        nonexistent = tmp_path / "nonexistent.csv"

        path, docs, error = process_single_file(nonexistent, read_csv)

        assert path == nonexistent
        assert len(docs) == 0
        assert error is not None

    def test_parallel_ingestion(self, tmp_path):
        """Test parallel ingestion of multiple files."""
        # Create test files
        for i in range(3):
            df = pd.DataFrame({"id": [i], "text": [f"Doc {i}"]})
            df.to_csv(tmp_path / f"file{i}.csv", index=False)

        # Change to tmp_path for cache file
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            docs = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                overwrite=True,
                max_workers=2,
                skip_cached=False
            )

            assert len(docs) == 3
        finally:
            os.chdir(original_cwd)

    def test_parallel_with_cache_skip(self, tmp_path):
        """Test parallel ingestion skips cached files."""
        df = pd.DataFrame({"id": [1], "text": ["Doc"]})
        csv_file = tmp_path / "cached.csv"
        df.to_csv(csv_file, index=False)

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # First run - should process
            docs1 = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                max_workers=1,
                skip_cached=True
            )
            assert len(docs1) == 1

            # Second run - should skip (cached)
            docs2 = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                max_workers=1,
                skip_cached=True
            )
            assert len(docs2) == 0
        finally:
            os.chdir(original_cwd)


class TestBatchProcessing:
    """Tests for batch processing mode."""

    def test_batch_ingestion(self, tmp_path):
        """Test batch ingestion yields documents in batches."""
        df = pd.DataFrame({
            "id": range(250),
            "text": [f"Doc {i}" for i in range(250)]
        })
        csv_file = tmp_path / "batch.csv"
        df.to_csv(csv_file, index=False)

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            batches = list(ingest_documents_batch(
                tmp_path,
                ["csv"],
                batch_size=100
            ))

            # Should have 3 batches (100, 100, 50)
            assert len(batches) == 3
            assert len(batches[0]) == 100
            assert len(batches[1]) == 100
            assert len(batches[2]) == 50
        finally:
            os.chdir(original_cwd)

    def test_batch_with_multiple_files(self, tmp_path):
        """Test batch processing with multiple files."""
        for i in range(2):
            df = pd.DataFrame({"id": range(60), "text": [f"Doc {i}_{j}" for j in range(60)]})
            df.to_csv(tmp_path / f"batch{i}.csv", index=False)

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            batches = list(ingest_documents_batch(
                tmp_path,
                ["csv"],
                batch_size=50,
                overwrite=True
            ))

            # Total 120 docs in batches of 50 = 3 batches (50, 50, 20)
            assert len(batches) == 3
            total_docs = sum(len(batch) for batch in batches)
            assert total_docs == 120
        finally:
            os.chdir(original_cwd)


class TestMemoryOptimization:
    """Tests for memory optimization features."""

    def test_generator_does_not_load_all(self, tmp_path):
        """Test that lazy reading doesn't load entire file into memory."""
        # Create large CSV
        df = pd.DataFrame({
            "id": range(10000),
            "text": [f"Document {i}" * 100 for i in range(10000)]
        })
        csv_file = tmp_path / "huge.csv"
        df.to_csv(csv_file, index=False)

        # Get generator
        gen = read_csv_lazy(csv_file, chunk_size=100)

        # Generator should be created without loading all data
        assert hasattr(gen, '__next__')

        # Get first chunk
        first_chunk = next(gen)
        assert len(first_chunk) == 100

        # Don't iterate through rest - memory efficient

    def test_batch_mode_memory_efficiency(self, tmp_path):
        """Test that batch mode processes without loading everything."""
        df = pd.DataFrame({
            "id": range(5000),
            "data": [f"Data {i}" for i in range(5000)]
        })
        csv_file = tmp_path / "memory_test.csv"
        df.to_csv(csv_file, index=False)

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Process in small batches
            batch_count = 0
            for batch in ingest_documents_batch(tmp_path, ["csv"], batch_size=100):
                batch_count += 1
                # Each batch should be manageable size
                assert len(batch) <= 100

            assert batch_count > 0
        finally:
            os.chdir(original_cwd)


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow_mixed_formats(self, tmp_path):
        """Test ingesting mixed file formats with all optimizations."""
        # Create test files
        pd.DataFrame({"id": [1, 2], "text": ["A", "B"]}).to_csv(tmp_path / "test.csv", index=False)
        pd.DataFrame({"id": [3, 4], "text": ["C", "D"]}).to_parquet(tmp_path / "test.parquet")
        with open(tmp_path / "test.jsonl", 'w') as f:
            f.write(json.dumps({"content": "E"}) + "\n")
            f.write(json.dumps({"content": "F"}) + "\n")

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            docs = ingest_documents_parallel(
                tmp_path,
                ["csv", "parquet", "jsonl"],
                overwrite=True,
                max_workers=2
            )

            assert len(docs) == 6
        finally:
            os.chdir(original_cwd)