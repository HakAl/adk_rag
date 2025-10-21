# Getting Started with VIBE Agent

Quick guide to get up and running with VIBE Code in minutes.

## Prerequisites

- **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- **Ollama** - [Download Ollama](https://ollama.com/)
- **Git** - For cloning the repository

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd rag_agent_app
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
.\venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### 4. Download AI Models

```bash
# Pull embedding model (for document processing)
ollama pull nomic-embed-text

# Pull chat model (for conversations)
ollama pull phi3:mini
```

This may take a few minutes depending on your internet connection.

## First Run

### 1. Add Documents

Create a `data/` directory and add your documents:

```bash
mkdir -p data
cp /path/to/your/documents/*.pdf data/
```

**Supported formats:** PDF, CSV, JSONL, Parquet

### 2. Ingest Documents

Process your documents into the vector store:

```bash
python scripts/ingest.py
```

You'll see progress as files are processed:
```
Processing documents...
✓ document1.pdf (150 chunks)
✓ document2.pdf (89 chunks)
Ingestion complete! Total: 239 chunks
```

### 3. Start Chatting

```bash
python main.py
```

You'll see:
```
RAG Agent CLI
Type 'exit' to quit, 'new' for new session, 'stats' for statistics

You: 
```

### 4. Ask Questions

```
You: What topics are covered in the documents?

Agent: Based on the documents, the main topics covered include...
[Answer with relevant sources]

You: Tell me more about X

Agent: [Detailed response]
```

## CLI Commands

While chatting, you can use these commands:

- **Regular message** - Just type your question
- **`stats`** - View system statistics
- **`new`** - Start a new conversation session
- **`exit`** or `quit` - Exit the application

## Optional: Configuration

Create a `.env` file for custom configuration:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Basic settings
ENVIRONMENT=development
LOG_LEVEL=INFO

# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
CHAT_MODEL=phi3:mini
```

## Optional: Add Cloud Providers

For enhanced capabilities, add API providers:

```bash
# In .env file
ANTHROPIC_API_KEY=your-key-here      # For complex reasoning
GOOGLE_API_KEY=your-key-here         # For fast responses
```

See [PROVIDERS.md](PROVIDERS.md) for detailed setup.

## Optional: Use REST API

Start the API server instead of CLI:

```bash
python run_api.py
```

Access at: http://localhost:8000/docs

See [API.md](API.md) for full API documentation.

## Optional: Docker Deployment

Run everything in containers:

```bash
# Start services
docker-compose up -d

# Ingest documents
docker-compose exec rag-agent python scripts/ingest.py

# View logs
docker-compose logs -f
```

See [DOCKER.md](DOCKER.md) for complete Docker guide.

## Verification Checklist

After setup, verify everything works:

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip list | grep langchain`)
- [ ] Ollama running (`curl http://localhost:11434/api/tags`)
- [ ] Models downloaded (`ollama list`)
- [ ] Documents in `data/` directory
- [ ] Ingestion completed successfully
- [ ] Chat interface responds to queries

## Common Issues

### Ollama Not Running

**Symptom:** `Connection refused` error

**Solution:**
```bash
# Start Ollama
ollama serve

# Or check if running
curl http://localhost:11434/api/tags
```

### Models Not Found

**Symptom:** `Model not found` error

**Solution:**
```bash
# List models
ollama list

# Pull missing models
ollama pull nomic-embed-text
ollama pull phi3:mini
```

### No Documents Found

**Symptom:** Ingestion finds 0 files

**Solution:**
```bash
# Check data directory
ls -R data/

# Verify file formats (PDF, CSV, JSONL, Parquet)
```

### Import Errors

**Symptom:** `ModuleNotFoundError`

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
pip install -e .

# Verify installation
pip list | grep -E "langchain|chromadb|ollama"
```

### Permission Errors

**Symptom:** `PermissionError` during ingestion

**Solution:**
```bash
# Fix permissions
chmod -R u+rw data/ chroma_db/
```

## Next Steps

Now that you're set up, explore:

1. **[Ingestion Guide](INGESTION.md)** - Advanced document processing options
2. **[API Reference](API.md)** - Build applications with the REST API
3. **[Docker Guide](DOCKER.md)** - Deploy in production
4. **[Providers Guide](PROVIDERS.md)** - Add Claude and Gemini
5. **[Architecture](ARCHITECTURE.md)** - Understand the system design

## Quick Reference

```bash
# Start chat
python main.py

# Start API
python run_api.py

# Ingest documents
python scripts/ingest.py

# Ingest with options
python scripts/ingest.py --workers 8 --batch-mode

# Run tests
pytest tests/

# Docker quick start
docker-compose up -d
make docker-ingest
```

## Getting Help

- **Documentation**: Check the `docs/` folder
- **Issues**: Open a GitHub issue
- **Logs**: Check `logs/rag_agent.log` if enabled
- **Stats**: Run `stats` command in CLI or check `/stats` API endpoint

## Project Structure

```
rag_agent_app/
├── app/                    # Application code
│   ├── api/               # REST API
│   ├── cli/               # CLI interface
│   ├── core/              # Core logic
│   └── services/          # Business services
├── config/                # Configuration
├── data/                  # Your documents (add here)
├── scripts/               # Utility scripts
├── tests/                 # Test suite
├── docs/                  # Documentation
├── main.py               # CLI entry point
└── run_api.py            # API entry point
```

## What's Next?

You're ready to:
- ✅ Ask questions about your documents
- ✅ Build applications with the API
- ✅ Deploy with Docker
- ✅ Add more providers for enhanced capabilities

Happy building! 🚀