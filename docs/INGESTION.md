# Document Ingestion Guide

Complete guide for processing and ingesting documents into the vector store.

## Supported Formats

- **PDF** (`.pdf`) - Text-based PDFs
- **CSV** (`.csv`) - Tabular data
- **JSONL** (`.jsonl`) - JSON lines format
- **Parquet** (`.parquet`) - Columnar data format

## Basic Usage

### Quick Start

```bash
# 1. Add documents to data/ directory
cp your-files/* data/

# 2. Run ingestion
python scripts/ingest.py
```

The script automatically:
- ✅ Recursively searches subdirectories
- ✅ Caches processed files (skips unchanged files)
- ✅ Processes files in parallel
- ✅ Shows progress with status updates

### Directory Structure

By default, ingestion searches recursively through all subdirectories:

```
data/
├── reports/
│   ├── 2024/
│   │   ├── Q1/
│   │   │   └── report.pdf
│   │   └── Q2/
│   └── 2023/
├── contracts/
│   └── client-agreements.pdf
└── archive/
    └── old-data.csv
```

All files will be found and processed automatically.

## Ingestion Options

### File Type Selection

```bash
# Ingest specific types
python scripts/ingest.py --types pdf csv

# Ingest all types (default)
python scripts/ingest.py --types all

# Available types: pdf, csv, jsonl, parquet
```

### Directory Configuration

```bash
# Use custom directory
python scripts/ingest.py --directory /path/to/documents

# Search only root directory (no subdirectories)
python scripts/ingest.py --no-recursive
```

### Performance Tuning

```bash
# Fast: More parallel workers
python scripts/ingest.py --workers 8

# Memory-efficient: Batch processing
python scripts/ingest.py --batch-mode --batch-size 50

# Combine both
python scripts/ingest.py --workers 8 --batch-mode
```

### Cache Management

```bash
# Normal: Use cache (skip unchanged files)
python scripts/ingest.py

# Force reprocess all files
python scripts/ingest.py --no-cache

# Start fresh (replace vector store)
python scripts/ingest.py --overwrite
```

## Performance Features

### 1. Parallel Processing
- Processes multiple files simultaneously
- Default: 4 workers
- Configurable: `--workers N`
- Best for: Multiple medium-sized files

### 2. File Caching
- Tracks file hashes in `.ingest_cache.json`
- Automatically skips unchanged files
- Speeds up subsequent ingestions
- Disable with: `--no-cache`

### 3. Batch Processing
- Memory-efficient for large datasets
- Processes in configurable batches
- Enable with: `--batch-mode`
- Configure with: `--batch-size N`

### 4. Lazy Loading
- Streams large files in chunks
- Prevents memory overflow
- Automatic for all formats

### 5. Recursive Search
- Searches all subdirectories by default
- Supports complex folder structures
- Disable with: `--no-recursive`

## Common Workflows

### Initial Ingestion

```bash
# Fast ingestion with parallel processing
python scripts/ingest.py --workers 8
```

### Incremental Updates

```bash
# Add new files to data/
cp new-docs/* data/

# Run ingestion (automatically skips cached files)
python scripts/ingest.py
```

### Large Datasets

```bash
# Memory-efficient processing
python scripts/ingest.py --batch-mode --batch-size 50 --workers 4
```

### Force Reprocessing

```bash
# Reprocess everything from scratch
python scripts/ingest.py --no-cache --overwrite
```

### Specific Directory

```bash
# Process files from custom location
python scripts/ingest.py --directory /mnt/documents --workers 8
```

### Only Root Directory

```bash
# Don't search subdirectories
python scripts/ingest.py --no-recursive
```

## Command Reference

```bash
python scripts/ingest.py [OPTIONS]

Options:
  --directory PATH              Data directory (default: ./data)
  --types TYPE [TYPE ...]       File types: pdf, csv, jsonl, parquet, all
  --workers N                   Parallel workers (default: 4)
  --batch-mode                  Use batch processing
  --batch-size N                Batch size (default: 100)
  --no-cache                    Disable file caching
  --no-recursive                Don't search subdirectories
  --overwrite                   Replace existing vector store
```

## File Processing Details

### PDF Files
- Extracts text from text-based PDFs
- Chunks text into manageable pieces
- Preserves document structure

### CSV Files
- Loads tabular data
- Converts rows to text representation
- Handles headers automatically

### JSONL Files
- Processes JSON objects line by line
- Memory-efficient streaming
- Handles large files

### Parquet Files
- Reads columnar data efficiently
- Converts to text representation
- Optimized for large datasets

## Troubleshooting

### Ingestion is Slow

**Solution 1**: Increase parallel workers
```bash
python scripts/ingest.py --workers 8
```

**Solution 2**: Use batch mode for large files
```bash
python scripts/ingest.py --batch-mode
```

### Out of Memory

**Solution**: Enable batch processing
```bash
python scripts/ingest.py --batch-mode --batch-size 50
```

### Cache Issues

**Solution**: Clear cache
```bash
rm .ingest_cache.json
python scripts/ingest.py --no-cache
```

### Files Not Found

**Check 1**: Verify directory
```bash
ls -R data/
```

**Check 2**: Ensure recursive search
```bash
# Remove --no-recursive if present
python scripts/ingest.py
```

### Permission Errors

**Solution**: Check file permissions
```bash
chmod -R u+r data/
```

## Best Practices

1. **Organize files logically** - Use subdirectories for categories
2. **Use caching** - Let incremental ingestion work for you
3. **Tune workers** - Match CPU core count for best performance
4. **Monitor memory** - Use batch mode for large datasets
5. **Test first** - Try ingestion on sample data before bulk processing
6. **Regular updates** - Run ingestion periodically for new documents

## Performance Guidelines

| Dataset Size | Files | Recommended Options |
|--------------|-------|-------------------|
| Small | < 100 | `--workers 4` |
| Medium | 100-1000 | `--workers 8` |
| Large | 1000-10000 | `--workers 8 --batch-mode` |
| Very Large | > 10000 | `--batch-mode --batch-size 50 --workers 4` |

## Docker Ingestion

```bash
# In Docker container
make docker-ingest

# Or with options
docker-compose exec rag-agent python scripts/ingest.py --workers 8
```