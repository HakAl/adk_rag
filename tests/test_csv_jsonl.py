"""
Tests for CSV and JSONL document ingestion.
"""
import pytest
import json
from pathlib import Path
import tempfile
import shutil

from app.services.vector_store import VectorStoreService
from config.settings import Settings


class TestCSVIngestion:
    """Test CSV file ingestion."""
    
    def test_load_csv_files(self, tmp_path):
        """Test loading CSV files."""
        # Create test CSV
        csv_content = """title,content,category
AI Basics,Introduction to AI,Technology
ML Guide,Machine learning overview,Technology"""
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        # Create service
        service = VectorStoreService()
        docs = service._load_csv_files(tmp_path)
        
        assert len(docs) == 2
        assert "AI Basics" in docs[0].page_content or "AI Basics" in docs[1].page_content
    
    def test_empty_csv_directory(self, tmp_path):
        """Test with no CSV files."""
        service = VectorStoreService()
        docs = service._load_csv_files(tmp_path)
        
        assert len(docs) == 0


class TestJSONLIngestion:
    """Test JSONL file ingestion."""
    
    def test_load_jsonl_files(self, tmp_path):
        """Test loading JSONL files."""
        # Create test JSONL
        jsonl_content = [
            {"text": "First entry about Python", "topic": "programming"},
            {"text": "Second entry about Docker", "topic": "devops"}
        ]
        
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, 'w') as f:
            for obj in jsonl_content:
                f.write(json.dumps(obj) + '\n')
        
        # Create service
        service = VectorStoreService()
        docs = service._load_jsonl_files(tmp_path)
        
        assert len(docs) == 2
        assert any("Python" in doc.page_content for doc in docs)
        assert any("Docker" in doc.page_content for doc in docs)
    
    def test_jsonl_with_content_field(self, tmp_path):
        """Test JSONL with 'content' field instead of 'text'."""
        jsonl_content = [
            {"content": "Content in content field", "category": "test"}
        ]
        
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, 'w') as f:
            for obj in jsonl_content:
                f.write(json.dumps(obj) + '\n')
        
        service = VectorStoreService()
        docs = service._load_jsonl_files(tmp_path)
        
        assert len(docs) == 1
        assert "Content in content field" in docs[0].page_content
    
    def test_jsonl_with_multiple_fields(self, tmp_path):
        """Test JSONL with multiple string fields."""
        jsonl_content = [
            {"field1": "Value 1", "field2": "Value 2", "number": 123}
        ]
        
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, 'w') as f:
            for obj in jsonl_content:
                f.write(json.dumps(obj) + '\n')
        
        service = VectorStoreService()
        docs = service._load_jsonl_files(tmp_path)
        
        assert len(docs) == 1
        # Should concatenate string fields
        content = docs[0].page_content
        assert "Value 1" in content
        assert "Value 2" in content
    
    def test_empty_jsonl_directory(self, tmp_path):
        """Test with no JSONL files."""
        service = VectorStoreService()
        docs = service._load_jsonl_files(tmp_path)
        
        assert len(docs) == 0
    
    def test_invalid_json_line_skipped(self, tmp_path):
        """Test that invalid JSON lines are skipped."""
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, 'w') as f:
            f.write('{"text": "Valid line"}\n')
            f.write('Invalid JSON line\n')
            f.write('{"text": "Another valid line"}\n')
        
        service = VectorStoreService()
        docs = service._load_jsonl_files(tmp_path)
        
        # Should have 2 valid documents
        assert len(docs) == 2


class TestTextExtraction:
    """Test text extraction from JSON."""
    
    def test_extract_text_standard_fields(self):
        """Test extraction from standard field names."""
        service = VectorStoreService()
        
        # Test 'text' field
        data = {"text": "This is text content", "meta": "metadata"}
        result = service._extract_text_from_json(data)
        assert result == "This is text content"
        
        # Test 'content' field
        data = {"content": "This is content", "meta": "metadata"}
        result = service._extract_text_from_json(data)
        assert result == "This is content"
    
    def test_extract_text_concatenation(self):
        """Test concatenation of multiple string fields."""
        service = VectorStoreService()
        
        data = {
            "field1": "Value 1",
            "field2": "Value 2",
            "number": 42
        }
        result = service._extract_text_from_json(data)
        
        assert "field1: Value 1" in result
        assert "field2: Value 2" in result


class TestMultiFormatIngestion:
    """Test ingesting multiple file formats together."""
    
    def test_ingest_mixed_formats(self, tmp_path):
        """Test ingesting CSV and JSONL together."""
        # Create CSV
        csv_content = """title,content
CSV Entry,This is from CSV"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        # Create JSONL
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, 'w') as f:
            f.write('{"text": "This is from JSONL"}\n')
        
        # Create service with temporary vector store
        temp_settings = Settings()
        temp_settings.vector_store_dir = tmp_path / "test_chroma"
        temp_settings.vector_store_dir.mkdir()
        
        service = VectorStoreService()
        service.embeddings = None  # Mock to avoid actual embedding
        
        # Test loading
        csv_docs = service._load_csv_files(tmp_path)
        jsonl_docs = service._load_jsonl_files(tmp_path)
        
        assert len(csv_docs) >= 1
        assert len(jsonl_docs) >= 1


# Run with: pytest tests/test_csv_jsonl.py -v
