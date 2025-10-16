"""
Unit tests for document ingestion, focusing on Parquet support.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from ingest import read_parquet, read_csv, read_jsonl


class TestParquetIngestion:
    """Tests for Parquet file ingestion."""

    def test_read_parquet_basic(self, tmp_path):
        """Test reading a basic Parquet file."""
        # Create test Parquet file
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "text": ["First document", "Second document", "Third document"],
            "category": ["A", "B", "A"]
        })
        parquet_file = tmp_path / "test.parquet"
        df.to_parquet(parquet_file)

        # Read documents
        documents = read_parquet(parquet_file)

        # Assertions
        assert len(documents) == 3
        assert all("content" in doc for doc in documents)
        assert all("metadata" in doc for doc in documents)
        assert "First document" in documents[0]["content"]
        assert documents[0]["metadata"]["source"] == str(parquet_file)
        assert documents[0]["metadata"]["row"] == 0

    def test_read_parquet_empty(self, tmp_path):
        """Test reading an empty Parquet file."""
        df = pd.DataFrame()
        parquet_file = tmp_path / "empty.parquet"
        df.to_parquet(parquet_file)

        documents = read_parquet(parquet_file)
        assert len(documents) == 0

    def test_read_parquet_various_types(self, tmp_path):
        """Test reading Parquet with various column types."""
        df = pd.DataFrame({
            "string_col": ["text1", "text2"],
            "int_col": [100, 200],
            "float_col": [1.5, 2.5],
            "bool_col": [True, False]
        })
        parquet_file = tmp_path / "types.parquet"
        df.to_parquet(parquet_file)

        documents = read_parquet(parquet_file)

        assert len(documents) == 2
        assert "string_col: text1" in documents[0]["content"]
        assert "int_col: 100" in documents[0]["content"]
        assert "float_col: 1.5" in documents[0]["content"]


class TestFormatConsistency:
    """Tests to ensure all formats produce consistent output structure."""

    def test_csv_parquet_consistency(self, tmp_path):
        """Test that CSV and Parquet produce similar document structures."""
        # Create identical data
        df = pd.DataFrame({
            "id": [1, 2],
            "content": ["Document A", "Document B"]
        })

        csv_file = tmp_path / "test.csv"
        parquet_file = tmp_path / "test.parquet"

        df.to_csv(csv_file, index=False)
        df.to_parquet(parquet_file)

        csv_docs = read_csv(csv_file)
        parquet_docs = read_parquet(parquet_file)

        # Both should have same number of documents
        assert len(csv_docs) == len(parquet_docs)

        # Both should have same structure
        for csv_doc, parquet_doc in zip(csv_docs, parquet_docs):
            assert set(csv_doc.keys()) == set(parquet_doc.keys())
            assert "content" in csv_doc and "content" in parquet_doc
            assert "metadata" in csv_doc and "metadata" in parquet_doc


class TestErrorHandling:
    """Tests for error handling in Parquet ingestion."""

    def test_read_parquet_nonexistent_file(self):
        """Test reading a non-existent Parquet file."""
        with pytest.raises(Exception):
            read_parquet(Path("nonexistent.parquet"))

    def test_read_parquet_invalid_file(self, tmp_path):
        """Test reading an invalid Parquet file."""
        invalid_file = tmp_path / "invalid.parquet"
        invalid_file.write_text("This is not a parquet file")

        with pytest.raises(Exception):
            read_parquet(invalid_file)