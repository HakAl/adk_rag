# CSV, JSONL, and Parquet Support Guide

The RAG Agent now supports ingesting data from CSV, JSONL, and Parquet files in addition to PDF documents.

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

### 4. Parquet Files (`.parquet`)
- Columnar storage format
- Efficient for large datasets
- Preserves data types and schema
- Each row becomes a document

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

## Parquet Format

### Basic Structure
Parquet is a columnar storage format that stores data efficiently in a binary format. Each row in the Parquet file becomes a document.

### Example: Analytics Data
```python
# Creating a Parquet file with pandas
import pandas as pd

data = {
    'title': ['API Design Best Practices', 'Database Optimization'],
    'content': ['RESTful API design involves...', 'Indexing strategies improve...'],
    'category': ['Backend', 'Database'],
    'views': [1250, 890]
}

df = pd.DataFrame(data)
df.to_parquet('knowledge_base.parquet', index=False)
```

**How it works:**
- Each row becomes a separate document
- All columns are read and concatenated for search
- Data types are preserved (strings, numbers, dates, etc.)
- Efficient for large datasets due to columnar compression
- Metadata from all columns is available

### Advantages of Parquet:
- **Efficient storage**: Compressed columnar format saves space
- **Fast reads**: Only needed columns are read
- **Type safety**: Preserves data types (integers, floats, dates)
- **Schema evolution**: Supports adding/removing columns
- **Big data ready**: Works well with large datasets

### Best Practices for Parquet:
1. **Use meaningful column names** (title, content, description, etc.)
2. **Keep text content in dedicated columns** for better organization
3. **Leverage data types** - Parquet preserves integers, dates, etc.
4. **Compress appropriately** - Default compression works well for most cases
5. **Consider partitioning** for very large datasets

### Common Use Cases:
- **Analytics exports**: Data from business intelligence tools
- **Machine learning datasets**: Training data with features
- **Log aggregations**: Processed logs from data pipelines
- **Database exports**: Efficient table exports
- **ETL outputs**: Transformed data from data pipelines

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

# Only Parquet
python scripts/ingest.py --types parquet

# Multiple types
python scripts/ingest.py --types pdf csv parquet

# All types (explicit)
python scripts/ingest.py --types all
```

### Other Options
```bash
# Custom directory
python scripts/ingest.py --directory /path/to/data --types csv jsonl parquet

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

### Parquet Use Cases
- **Data warehouse exports**: Analytics data from warehouses
- **ML feature stores**: Prepared features for models
- **Time-series data**: Metrics and events with timestamps
- **Large-scale knowledge bases**: Millions of documents
- **ETL pipeline outputs**: Processed data from pipelines
- **Database snapshots**: Efficient table exports

## Example Files

Example files are provided in the `examples/` directory:

- `sample_knowledge.csv` - Example CSV with tech topics
- `sample_knowledge.jsonl` - Example JSONL with programming concepts
- `sample_knowledge.parquet` - Example Parquet with data analytics topics

### Test the Examples
```bash
# Copy examples to data directory
cp examples/sample_knowledge.csv data/
cp examples/sample_knowledge.jsonl data/
cp examples/sample_knowledge.parquet data/

# Ingest
python scripts/ingest.py --types csv jsonl parquet

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
    file_types=['csv', 'jsonl', 'parquet'],
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
    file_types=['pdf', 'csv', 'jsonl', 'parquet'],
    overwrite=False
)
```

### Creating Parquet Files

```python
import pandas as pd

# From a DataFrame
df = pd.DataFrame({
    'title': ['Topic 1', 'Topic 2'],
    'content': ['Content 1...', 'Content 2...'],
    'category': ['Tech', 'Science']
})
df.to_parquet('data/my_knowledge.parquet', index=False)

# From CSV
df = pd.read_csv('data.csv')
df.to_parquet('data.parquet', index=False)

# From JSONL
df = pd.read_json('data.jsonl', lines=True)
df.to_parquet('data.parquet', index=False)
```

## Tips for Optimal Results

### Data Preparation
1. **Clean your data**: Remove duplicates and irrelevant information
2. **Consistent formatting**: Use consistent column names and JSON fields
3. **Chunk size**: Large CSV rows, JSON objects, or Parquet rows will be automatically chunked
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

### Parquet Tips
- Use a `content` or `text` column for main searchable text
- Keep structured metadata in separate columns
- Leverage compression for large files
- Use appropriate data types (dates as datetime, not strings)
- Consider splitting very large files (>100MB) into smaller partitions

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

### Parquet Issues

**Problem**: Parquet file not loading
- Verify file is valid Parquet format
- Check if pandas/pyarrow is installed
- Ensure file isn't corrupted

**Problem**: Missing dependencies
- Install required libraries: `pip install pandas pyarrow`
- Or use: `pip install fastparquet` as alternative

**Problem**: Memory issues with large files
- Process in smaller batches
- Use row group filtering if possible
- Consider splitting into multiple smaller files

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

- **Large CSVs**: Consider converting to Parquet for better performance
- **Many JSONL records**: Ingestion happens line-by-line, so memory efficient
- **Parquet files**: Most efficient for large datasets, faster reads than CSV
- **Mixed file types**: All are processed in a single batch for efficiency
- **Chunking**: Large documents are automatically split into optimal chunks
- **File size**: Parquet files are typically 50-80% smaller than equivalent CSV files

## Format Comparison

| Feature | CSV | JSONL | Parquet |
|---------|-----|-------|---------|
| **Human Readable** | ✅ Yes | ✅ Yes | ❌ No (binary) |
| **Compression** | ❌ Manual | ❌ Manual | ✅ Built-in |
| **Type Safety** | ❌ No | ⚠️ Partial | ✅ Yes |
| **Schema Evolution** | ❌ No | ✅ Yes | ✅ Yes |
| **Large Files** | ⚠️ Slow | ✅ Fast | ✅ Very Fast |
| **Nested Data** | ❌ No | ✅ Yes | ✅ Yes |
| **Best For** | Small datasets | API data, logs | Analytics, ML |

## Next Steps

1. Prepare your CSV, JSONL, or Parquet files
2. Place them in the `data/` directory
3. Run ingestion with appropriate file type flags
4. Query your data through the chat interface

For more information, see the main [README.md](../README.md).