# CSV and JSONL Support Guide

The RAG Agent now supports ingesting data from CSV and JSONL files in addition to PDF documents.

## Supported File Formats

### 1. PDF Files (`.pdf`)
- Standard PDF documents
- Automatically extracted text content
- Preserves page structure

### 2. CSV Files (`.csv`)
- Comma-separated values
- Each row becomes a document
- All columns are included in the searchable content

### 3. JSONL Files (`.jsonl`, `.json`)
- JSON Lines format (one JSON object per line)
- Flexible schema - automatically extracts text from various fields
- Supports nested structures

## CSV Format

### Basic Structure
```csv
column1,column2,column3
value1,value2,value3
value4,value5,value6
```

### Example: Knowledge Base
```csv
title,content,category,author
Introduction to AI,Artificial intelligence is...,Technology,John Doe
Machine Learning,Machine learning involves...,Technology,Jane Smith
```

**How it works:**
- Each row becomes a separate document
- All columns are concatenated for search
- Metadata is preserved

### Best Practices for CSV:
1. **Include a header row** with column names
2. **Use meaningful column names** (title, content, description, etc.)
3. **Keep content in dedicated columns** for better organization
4. **Use UTF-8 encoding** to support special characters
5. **Escape commas** within values with quotes

## JSONL Format

### Basic Structure
Each line is a valid JSON object:

```jsonl
{"field1": "value1", "field2": "value2"}
{"field1": "value3", "field2": "value4"}
```

### Example: Tech Documentation
```jsonl
{"text": "Python is a high-level programming language...", "topic": "programming", "difficulty": "beginner"}
{"text": "Docker is a containerization platform...", "topic": "devops", "difficulty": "intermediate"}
{"content": "Kubernetes orchestrates containers...", "category": "infrastructure", "level": "advanced"}
```

**How it works:**
- Each line is parsed as a separate JSON object
- Text is extracted from common fields: `text`, `content`, `body`, `message`, `description`, `summary`
- If no standard field is found, all string fields are concatenated
- Original JSON data is preserved in metadata

### Field Priority (for text extraction):
1. `text`
2. `content`
3. `body`
4. `message`
5. `description`
6. `summary`
7. All other string fields (concatenated)

### Best Practices for JSONL:
1. **Use standard field names** (`text`, `content`) for main content
2. **Keep one JSON object per line** (no multi-line objects)
3. **Include metadata** in separate fields
4. **Use UTF-8 encoding**
5. **Validate JSON** before ingestion

## Ingestion Commands

### Ingest All File Types (Default)
```bash
python scripts/ingest.py
```

### Ingest Specific File Types
```bash
# Only PDFs
python scripts/ingest.py --types pdf

# Only CSVs
python scripts/ingest.py --types csv

# Only JSONL
python scripts/ingest.py --types jsonl

# Multiple types
python scripts/ingest.py --types pdf csv

# All types (explicit)
python scripts/ingest.py --types all
```

### Other Options
```bash
# Custom directory
python scripts/ingest.py --directory /path/to/data --types csv jsonl

# Overwrite existing data
python scripts/ingest.py --overwrite --types all
```

## Use Cases

### CSV Use Cases
- **FAQ databases**: Question, Answer, Category columns
- **Product catalogs**: Name, Description, Features columns
- **Knowledge articles**: Title, Content, Tags columns
- **Training data**: Input, Output, Context columns
- **Customer data**: Issue, Resolution, Category columns

### JSONL Use Cases
- **API responses**: Structured data from external APIs
- **Log data**: Application logs with metadata
- **Social media**: Tweets, posts with engagement metrics
- **Documentation**: Code snippets with explanations
- **Chat transcripts**: Messages with timestamps and users

## Example Files

Example files are provided in the `examples/` directory:

- `sample_knowledge.csv` - Example CSV with tech topics
- `sample_knowledge.jsonl` - Example JSONL with programming concepts

### Test the Examples
```bash
# Copy examples to data directory
cp examples/sample_knowledge.csv data/
cp examples/sample_knowledge.jsonl data/

# Ingest
python scripts/ingest.py --types csv jsonl

# Query
python main.py
# Then ask: "What is Python?"
```

## Programmatic Usage

### In Python Code

```python
from app.core.application import RAGAgentApp
from pathlib import Path

app = RAGAgentApp()

# Ingest all types
num_docs, num_chunks, files = app.ingest_documents()

# Ingest specific types
num_docs, num_chunks, files = app.ingest_documents(
    directory=Path("data"),
    file_types=['csv', 'jsonl'],
    overwrite=False
)
```

### Direct Service Access

```python
from app.services.vector_store import VectorStoreService

vector_store = VectorStoreService()

# Ingest documents
num_docs, num_chunks, files = vector_store.ingest_documents(
    directory=Path("data"),
    file_types=['pdf', 'csv', 'jsonl'],
    overwrite=False
)
```

## Tips for Optimal Results

### Data Preparation
1. **Clean your data**: Remove duplicates and irrelevant information
2. **Consistent formatting**: Use consistent column names and JSON fields
3. **Chunk size**: Large CSV rows or JSON objects will be automatically chunked
4. **Metadata**: Include metadata fields for better context

### CSV Tips
- Keep the main content in a dedicated column (e.g., "content" or "description")
- Use additional columns for metadata (category, author, date)
- Avoid extremely long text in single cells

### JSONL Tips
- Use the `text` or `content` field for main content
- Store metadata in separate fields
- Keep objects relatively flat (avoid deep nesting)
- Each line should be a complete, valid JSON object

## Troubleshooting

### CSV Issues

**Problem**: CSV not loading
- Check encoding (should be UTF-8)
- Verify commas are properly escaped
- Ensure header row exists

**Problem**: Strange characters appear
- Use UTF-8 encoding when saving CSV
- Check for BOM (Byte Order Mark) issues

### JSONL Issues

**Problem**: JSONL not loading
- Verify each line is valid JSON
- Check for trailing commas
- Ensure UTF-8 encoding

**Problem**: No text extracted
- Use standard field names (`text`, `content`)
- Check JSON structure
- Verify string values aren't empty

## Advanced: Custom Text Extraction

For custom JSON structures, you can modify `_extract_text_from_json()` in `app/services/vector_store.py`:

```python
def _extract_text_from_json(self, data: Dict[str, Any]) -> str:
    # Your custom logic here
    # Example: extract from nested structure
    if 'article' in data and 'body' in data['article']:
        return data['article']['body']
    
    # Fall back to default behavior
    return super()._extract_text_from_json(data)
```

## Performance Considerations

- **Large CSVs**: Consider splitting into smaller files
- **Many JSONL records**: Ingestion happens line-by-line, so memory efficient
- **Mixed file types**: All are processed in a single batch for efficiency
- **Chunking**: Large documents are automatically split into optimal chunks

## Next Steps

1. Prepare your CSV or JSONL files
2. Place them in the `data/` directory
3. Run ingestion with appropriate file type flags
4. Query your data through the chat interface

For more information, see the main [README.md](../README.md).
