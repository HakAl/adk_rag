# VIBE Agent

A maintainable Python application for Retrieval-Augmented Generation (RAG) using Google's Agent Development Kit (ADK) and Ollama for local LLM inference.

**Key Features:**
- Multiple document formats (PDF, CSV, JSONL, Parquet)
- Local-first with optional cloud providers (Anthropic Claude, Google Gemini)
- Performance optimized (parallel processing, caching, batch mode)
- REST API and CLI interfaces
- Docker deployment ready

## Quick Start

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com/)

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd rag_agent_app
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Download models
ollama pull nomic-embed-text
ollama pull phi3:mini
```

### Basic Usage

```bash
# 1. Add documents to data/ directory
cp your-pdfs/*.pdf data/

# 2. Ingest documents
python scripts/ingest.py

# 3. Start chat interface
python main.py

# Or start REST API
python run_api.py
```

## Documentation

- **[Getting Started Guide](docs/GETTING_STARTED.md)** - Installation and first steps
- **[Docker Deployment](docs/DOCKER.md)** - Container deployment guide
- **[REST API](docs/API.md)** - API reference and examples
- **[Ingestion Guide](docs/INGESTION.md)** - Document processing options
- **[Multi-Provider Setup](docs/PROVIDERS.md)** - Configure Claude and Gemini
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Development](docs/DEVELOPMENT.md)** - Contributing and code style

## Architecture

```
rag_agent_app/
├── app/
│   ├── core/           # Core application logic
│   ├── services/       # Business logic services
│   ├── models/         # Data models
│   ├── cli/            # Command-line interface
│   └── api/            # REST API
├── config/             # Configuration
├── scripts/            # Utility scripts
├── tests/              # Test suite
├── data/               # Documents (gitignored)
├── chroma_db/          # Vector store (gitignored)
└── docs/               # Documentation
```

## Key Commands

```bash
# Ingestion
python scripts/ingest.py                    # Basic ingestion
python scripts/ingest.py --workers 8        # Parallel processing
python scripts/ingest.py --batch-mode       # Memory-efficient

# Interfaces
python main.py                              # CLI chat
python run_api.py                           # REST API server

# Docker
docker-compose up -d                        # Start stack
make docker-setup                           # Complete setup
make docker-ingest                          # Ingest in container

# Testing
pytest tests/                               # Run all tests
pytest --cov=app --cov-report=html         # With coverage
```

## Configuration

Create a `.env` file:

```bash
# Required
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
CHAT_MODEL=phi3:mini

# Optional: Cloud providers
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Optional: Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Support & Contributing

- **Issues**: Open a GitHub issue
- **Contributing**: See [DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **License**: [Your License Here]

---

**Need help?** Start with the [Getting Started Guide](docs/GETTING_STARTED.md)