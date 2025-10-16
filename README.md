# RAG Agent - Production-Ready Python Application

A maintainable, production-ready Python application for Retrieval-Augmented Generation (RAG) using Google's Agent Development Kit (ADK) and Ollama for local LLM inference.

**Supports multiple document formats**: PDF, CSV, JSONL, and Parquet files.

**Performance Optimizations**: Parallel processing, batch processing, lazy loading, file caching, and memory optimization.

## 🏗️ Architecture

This application follows clean architecture principles with clear separation of concerns:

```
rag_agent_app/
├── app/
│   ├── core/           # Core application logic
│   ├── services/       # Business logic services
│   ├── models/         # Data models
│   └── cli/            # Command-line interface
├── config/             # Configuration and settings
├── scripts/            # Utility scripts
├── tests/              # Test suite
├── data/               # PDF documents (gitignored)
├── chroma_db/          # Vector store (gitignored)
└── logs/               # Application logs (gitignored)
```

### Key Components

- **VectorStoreService**: Manages document embeddings and similarity search using ChromaDB
- **RAGService**: Handles retrieval and answer generation using LiteLLM
- **ADKAgentService**: Orchestrates the Google ADK agent with tool integration
- **RAGAgentApp**: Main application class that coordinates all services
- **CLI**: Interactive command-line interface

## 🚀 Getting Started

### Prerequisites

1. **Ollama** - Install from [ollama.com](https://ollama.com/)
2. **Python 3.9+** - Required for the application
3. **Local LLM Models** - Download via Ollama

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd rag_agent_app
```

2. **Create virtual environment**
```bash
python -m venv venv

# On macOS/Linux
source venv/bin/activate

# On Windows
.\venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download Ollama models**
```bash
ollama pull nomic-embed-text
ollama pull llama3.1:8b-instruct-q4_K_M
```

5. **Configure environment** (optional)
```bash
cp .env.example .env
# Edit .env with your preferences
```

## 📖 Usage

### 1. Ingest Documents

Place your documents in the `data/` directory:
- PDF files (`.pdf`)
- CSV files (`.csv`)
- JSONL files (`.jsonl`)
- Parquet files (`.parquet`)

Then run:

```bash
# Basic ingestion (parallel, with caching)
python scripts/ingest.py

# Ingest specific file types
python scripts/ingest.py --types pdf csv jsonl parquet

# Ingest from custom directory
python scripts/ingest.py --directory /path/to/documents

# Use more workers for faster processing
python scripts/ingest.py --workers 8

# Batch mode for memory-efficient processing
python scripts/ingest.py --batch-mode --batch-size 50

# Disable caching to reprocess all files
python scripts/ingest.py --no-cache

# Overwrite existing vector store
python scripts/ingest.py --overwrite
```

**Performance Options:**
- `--directory PATH`: Specify a different data directory
- `--types TYPE [TYPE ...]`: Specify file types (pdf, csv, jsonl, parquet, or all)
- `--workers N`: Number of parallel workers (default: 4)
- `--batch-mode`: Use batch processing for memory efficiency
- `--batch-size N`: Batch size for batch mode (default: 100)
- `--no-cache`: Disable file caching (process all files)
- `--overwrite`: Replace existing vector store collection

**Example Workflows:**

```bash
# Fast ingestion with 8 parallel workers
python scripts/ingest.py --workers 8

# Memory-efficient ingestion of large files
python scripts/ingest.py --batch-mode --batch-size 50

# Re-ingest only modified files (automatic with caching)
python scripts/ingest.py

# Force re-ingestion of all files
python scripts/ingest.py --no-cache --overwrite
```

### 2. Start Chat Interface

```bash
python main.py
```

### Interactive Commands

- **Regular chat**: Just type your question
- **`stats`**: View application statistics
- **`new`**: Start a new conversation session
- **`exit`** or **`quit`**: Exit the application

## ⚡ Performance Features

### 1. Parallel Processing
- Processes multiple files simultaneously using `ProcessPoolExecutor`
- Configurable number of workers (default: 4)
- Significantly faster for multiple files

### 2. File Caching
- Tracks file hashes to skip unchanged files
- Stored in `.ingest_cache.json`
- Automatic incremental ingestion
- Use `--no-cache` to disable

### 3. Lazy Loading
- Streams large files in chunks
- Prevents memory overflow on large datasets
- Configurable chunk sizes for each format

### 4. Batch Processing
- Memory-efficient mode for very large datasets
- Processes documents in batches
- Use `--batch-mode` flag

### 5. Memory Optimization
- Uses generators instead of loading entire files
- Clears processed chunks from memory
- Suitable for datasets larger than available RAM

## 🛠️ Configuration

Configuration is managed through `config/settings.py` and can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | development | Environment name |
| `DEBUG` | false | Enable debug logging |
| `OLLAMA_BASE_URL` | http://localhost:11434 | Ollama server URL |
| `EMBEDDING_MODEL` | nomic-embed-text | Model for embeddings |
| `CHAT_MODEL` | llama3.1:8b-instruct-q4_K_M | Model for chat |
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_TO_FILE` | false | Enable file logging |

## 🏢 Production Deployment

### Environment-Specific Settings

The application supports multiple environments:

```python
# Development (default)
ENVIRONMENT=development

# Production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
LOG_TO_FILE=true
```

### Best Practices

1. **Use environment variables** for configuration
2. **Enable file logging** in production
3. **Set appropriate log levels** (WARNING or ERROR for production)
4. **Monitor Ollama service** health
5. **Backup vector store** regularly
6. **Use parallel processing** for faster ingestion
7. **Enable caching** to avoid reprocessing unchanged files

### Docker Deployment (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pull models
RUN ollama serve & \
    sleep 5 && \
    ollama pull nomic-embed-text && \
    ollama pull llama3.1:8b-instruct-q4_K_M

CMD ["python", "main.py"]
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_optimized_ingestion.py

# Run with coverage
pytest tests/unit/ --cov=scripts --cov-report=html
```

### Integration Tests

```bash
pytest tests/integration/
```

### Test Coverage

```bash
pytest --cov=app --cov=scripts --cov-report=html
```

## 📊 Monitoring and Logging

### View Logs

```bash
# Console logs (default)
# Logs appear in stdout

# File logs (if LOG_TO_FILE=true)
tail -f logs/rag_agent.log
```

### Application Statistics

```python
from app.core.application import RAGAgentApp

app = RAGAgentApp()
stats = app.get_stats()
print(stats)
```

## 🔧 Development

### Project Structure

```
app/
├── core/
│   └── application.py      # Main app orchestration
├── services/
│   ├── vector_store.py     # Vector DB operations
│   ├── rag.py              # RAG query handling
│   └── adk_agent.py        # ADK agent management
├── models/
│   └── schemas.py          # Data models (for future API)
└── cli/
    └── chat.py             # CLI interface
```

### Adding New Features

1. **New service**: Add to `app/services/`
2. **New CLI command**: Modify `app/cli/chat.py`
3. **New script**: Add to `scripts/`
4. **Configuration**: Update `config/settings.py`

### Code Style

```bash
# Format code
black app/ config/ scripts/

# Check linting
pylint app/ config/ scripts/

# Type checking
mypy app/ config/ scripts/
```

## 🐛 Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### Vector Store Issues

```bash
# Clear and rebuild vector store
python scripts/ingest.py --overwrite --no-cache
```

### Model Not Found

```bash
# List available models
ollama list

# Pull required models
ollama pull nomic-embed-text
ollama pull llama3.1:8b-instruct-q4_K_M
```

### Ingestion Cache Issues

```bash
# Clear ingestion cache
rm .ingest_cache.json

# Re-ingest all files
python scripts/ingest.py --no-cache
```

### Performance Issues

```bash
# Increase parallel workers
python scripts/ingest.py --workers 8

# Use batch mode for large datasets
python scripts/ingest.py --batch-mode --batch-size 50
```

## 📝 Next Steps

This application is ready to be extended with:

1. **Flask REST API** - Add API endpoints for web/mobile clients
2. **React Frontend** - Build a modern web interface
3. **Authentication** - Add user management
4. **Multi-tenancy** - Support multiple users/organizations
5. **Advanced RAG** - Implement hybrid search, re-ranking
6. **Observability** - Add Prometheus metrics, OpenTelemetry
7. **GPU Acceleration** - Support GPU for embeddings

## 📄 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please follow the existing code structure and add tests for new features.

## 📧 Support

For issues and questions, please open a GitHub issue or contact the development team.