"""
Unit tests for recursive subdirectory ingestion.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from ingest import ingest_documents_parallel, ingest_documents_batch


class TestRecursiveIngestion:
    """Tests for recursive subdirectory ingestion."""

    def test_recursive_finds_subdirectory_files(self, tmp_path):
        """Test that recursive mode finds files in subdirectories."""
        # Create files in subdirectories
        (tmp_path / "sub1").mkdir()
        (tmp_path / "sub2").mkdir()
        (tmp_path / "sub1" / "nested").mkdir()

        # Create CSV files
        pd.DataFrame({"id": [1], "text": ["Root"]}).to_csv(tmp_path / "root.csv", index=False)
        pd.DataFrame({"id": [2], "text": ["Sub1"]}).to_csv(tmp_path / "sub1" / "file1.csv", index=False)
        pd.DataFrame({"id": [3], "text": ["Sub2"]}).to_csv(tmp_path / "sub2" / "file2.csv", index=False)
        pd.DataFrame({"id": [4], "text": ["Nested"]}).to_csv(tmp_path / "sub1" / "nested" / "file3.csv", index=False)

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            docs = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                overwrite=True,
                max_workers=2,
                skip_cached=False,
                recursive=True
            )

            # Should find all 4 files
            assert len(docs) == 4
        finally:
            os.chdir(original_cwd)

    def test_non_recursive_only_finds_root(self, tmp_path):
        """Test that non-recursive mode only finds root directory files."""
        # Create files in subdirectories
        (tmp_path / "sub1").mkdir()

        # Create CSV files
        pd.DataFrame({"id": [1], "text": ["Root"]}).to_csv(tmp_path / "root.csv", index=False)
        pd.DataFrame({"id": [2], "text": ["Sub1"]}).to_csv(tmp_path / "sub1" / "file1.csv", index=False)

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            docs = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                overwrite=True,
                max_workers=2,
                skip_cached=False,
                recursive=False
            )

            # Should only find 1 file in root
            assert len(docs) == 1
            assert "Root" in docs[0]["content"]
        finally:
            os.chdir(original_cwd)

    def test_recursive_mixed_formats(self, tmp_path):
        """Test recursive ingestion with mixed file formats."""
        # Create subdirectories
        (tmp_path / "pdfs").mkdir()
        (tmp_path / "data").mkdir()

        # Create different file types in subdirectories
        pd.DataFrame({"id": [1], "text": ["CSV"]}).to_csv(tmp_path / "data" / "test.csv", index=False)
        pd.DataFrame({"id": [2], "text": ["Parquet"]}).to_parquet(tmp_path / "data" / "test.parquet")

        with open(tmp_path / "data" / "test.jsonl", 'w') as f:
            f.write(json.dumps({"content": "JSONL"}) + "\n")

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            docs = ingest_documents_parallel(
                tmp_path,
                ["csv", "parquet", "jsonl"],
                overwrite=True,
                recursive=True
            )

            # Should find all 3 files
            assert len(docs) == 3
        finally:
            os.chdir(original_cwd)

    def test_recursive_deep_nesting(self, tmp_path):
        """Test recursive ingestion with deeply nested directories."""
        # Create deep directory structure
        deep_path = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True)

        # Create file at deepest level
        pd.DataFrame({"id": [1], "text": ["Deep"]}).to_csv(deep_path / "deep.csv", index=False)

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            docs = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                overwrite=True,
                recursive=True
            )

            # Should find file in deeply nested directory
            assert len(docs) == 1
            assert "Deep" in docs[0]["content"]
        finally:
            os.chdir(original_cwd)

    def test_recursive_batch_mode(self, tmp_path):
        """Test recursive ingestion in batch mode."""
        # Create subdirectories with files
        (tmp_path / "sub1").mkdir()
        (tmp_path / "sub2").mkdir()

        pd.DataFrame({"id": range(50), "text": [f"Doc{i}" for i in range(50)]}).to_csv(
            tmp_path / "sub1" / "batch1.csv", index=False
        )
        pd.DataFrame({"id": range(50, 100), "text": [f"Doc{i}" for i in range(50, 100)]}).to_csv(
            tmp_path / "sub2" / "batch2.csv", index=False
        )

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            batches = list(ingest_documents_batch(
                tmp_path,
                ["csv"],
                batch_size=30,
                recursive=True
            ))

            # Should find both files and process in batches
            total_docs = sum(len(batch) for batch in batches)
            assert total_docs == 100
            assert len(batches) > 1  # Should be multiple batches
        finally:
            os.chdir(original_cwd)

    def test_recursive_with_empty_subdirectories(self, tmp_path):
        """Test recursive ingestion handles empty subdirectories."""
        # Create empty and non-empty subdirectories
        (tmp_path / "empty1").mkdir()
        (tmp_path / "empty2").mkdir()
        (tmp_path / "with_files").mkdir()

        pd.DataFrame({"id": [1], "text": ["Data"]}).to_csv(
            tmp_path / "with_files" / "file.csv", index=False
        )

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            docs = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                overwrite=True,
                recursive=True
            )

            # Should only find file in non-empty directory
            assert len(docs) == 1
        finally:
            os.chdir(original_cwd)

    def test_recursive_metadata_includes_path(self, tmp_path):
        """Test that metadata includes full path for files in subdirectories."""
        (tmp_path / "subdir").mkdir()

        pd.DataFrame({"id": [1], "text": ["Test"]}).to_csv(
            tmp_path / "subdir" / "test.csv", index=False
        )

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            docs = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                overwrite=True,
                recursive=True
            )

            # Metadata should contain full path including subdirectory
            assert len(docs) == 1
            assert "subdir" in docs[0]["metadata"]["source"]
        finally:
            os.chdir(original_cwd)

    def test_recursive_cache_works_across_subdirectories(self, tmp_path):
        """Test that caching works correctly with subdirectories."""
        (tmp_path / "sub1").mkdir()
        (tmp_path / "sub2").mkdir()

        pd.DataFrame({"id": [1], "text": ["File1"]}).to_csv(tmp_path / "sub1" / "f1.csv", index=False)
        pd.DataFrame({"id": [2], "text": ["File2"]}).to_csv(tmp_path / "sub2" / "f2.csv", index=False)

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # First run - should process both
            docs1 = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                recursive=True,
                skip_cached=True
            )
            assert len(docs1) == 2

            # Second run - should skip both (cached)
            docs2 = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                recursive=True,
                skip_cached=True
            )
            assert len(docs2) == 0
        finally:
            os.chdir(original_cwd)


class TestRecursiveIntegration:
    """Integration tests for recursive ingestion."""

    def test_complex_directory_structure(self, tmp_path):
        """Test with realistic complex directory structure."""
        # Create structure like: data/2024/01/, data/2024/02/, data/2023/12/
        (tmp_path / "2024" / "01").mkdir(parents=True)
        (tmp_path / "2024" / "02").mkdir(parents=True)
        (tmp_path / "2023" / "12").mkdir(parents=True)

        # Create files in each directory
        pd.DataFrame({"id": [1], "text": ["Jan2024"]}).to_csv(
            tmp_path / "2024" / "01" / "jan.csv", index=False
        )
        pd.DataFrame({"id": [2], "text": ["Feb2024"]}).to_csv(
            tmp_path / "2024" / "02" / "feb.csv", index=False
        )
        pd.DataFrame({"id": [3], "text": ["Dec2023"]}).to_csv(
            tmp_path / "2023" / "12" / "dec.csv", index=False
        )

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            docs = ingest_documents_parallel(
                tmp_path,
                ["csv"],
                overwrite=True,
                recursive=True
            )

            # Should find all 3 files across directory structure
            assert len(docs) == 3

            # Verify content from different directories
            contents = [doc["content"] for doc in docs]
            assert any("Jan2024" in c for c in contents)
            assert any("Feb2024" in c for c in contents)
            assert any("Dec2023" in c for c in contents)
        finally:
            os.chdir(original_cwd)