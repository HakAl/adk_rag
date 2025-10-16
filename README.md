# VIBE Agent

A maintainable, Python application for Retrieval-Augmented Generation (RAG) using Google's Agent Development Kit (ADK) and Ollama for local LLM inference.

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

pip install -e .
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

**Note**: By default, ingestion searches recursively through all subdirectories. You can organize files in subdirectories like `data/2024/reports/`, `data/archive/`, etc.

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
- `--no-recursive`: Search only the root directory, not subdirectories
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

# Ingest only from root directory (no subdirectories)
python scripts/ingest.py --no-recursive

# Ingest from complex subdirectory structure (default behavior)
# Automatically finds files in data/2024/Q1/, data/archive/, etc.
python scripts/ingest.py
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

### 6. Recursive Subdirectory Search
- Automatically searches all subdirectories (default)
- Supports complex directory structures
- Use `--no-recursive` to search only root directory

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

# Docker Deployment

The application includes a complete Docker Compose setup for running the entire stack in containers.

## 🐳 Quick Start with Docker

### Prerequisites

- Docker Engine 20.10+
- Docker Compose V2
- (Optional) NVIDIA Docker runtime for GPU support

### 1. Clone and Configure

```bash
git clone <repository-url>
cd adk_rag

# Copy and configure environment
cp .env.docker .env
# Edit .env with your settings (optional)
```

### 2. Start the Stack

**Production Mode:**
```bash
# Build and start all services
docker-compose up -d

# Or use Make
make docker-up
```

**Development Mode (with hot reload):**
```bash
# Use development compose file
docker-compose -f docker-compose.dev.yml up -d

# Or use Make
make docker-dev
```

This will start:
- **Ollama service** on port 11434
- **RAG Agent application** on port 8000

### 3. Pull Models (First Time)

The models are pulled automatically on first startup. To manually pull models:

```bash
# Using docker-compose
docker-compose exec ollama ollama pull nomic-embed-text
docker-compose exec ollama ollama pull llama3.1:8b-instruct-q4_K_M

# Or using Make
make docker-pull-models
```

### 4. Ingest Documents

```bash
# Place documents in ./data directory
mkdir -p data
cp /path/to/your/pdfs/* data/

# Run ingestion
docker-compose exec rag-agent python scripts/ingest.py

# Or using Make
make docker-ingest
```

### 5. Access the Application

```bash
# View logs
docker-compose logs -f rag-agent

# Or using Make
make docker-logs-app
```

## 🔧 Development vs Production

### Development Mode

**File**: `docker-compose.dev.yml`

**Features**:
- Hot reload - code changes reflect immediately
- Source code mounted as volumes
- Debug logging enabled
- Faster iteration

**Usage**:
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Stop
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Rebuild after dependency changes
docker-compose -f docker-compose.dev.yml up --build
```

**When to use**: Local development, testing changes

### Production Mode

**File**: `docker-compose.yml`

**Features**:
- Optimized for performance
- Production logging
- Automatic restarts
- Resource limits
- Health checks

**Usage**:
```bash
# Start production environment
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f
```

**When to use**: Deployment, production environments

## 🛠️ Docker Commands

### Development Mode Commands

```bash
# Start development environment (with logs visible)
docker-compose -f docker-compose.dev.yml up
# Or: make docker-dev

# Start in background
docker-compose -f docker-compose.dev.yml up -d
# Or: make docker-dev-up

# Stop services
docker-compose -f docker-compose.dev.yml down
# Or: make docker-dev-down

# View logs
docker-compose -f docker-compose.dev.yml logs -f
# Or: make docker-dev-logs

# Restart after code changes (usually not needed with hot reload)
docker-compose -f docker-compose.dev.yml restart
# Or: make docker-dev-restart

# Access shell
docker-compose -f docker-compose.dev.yml exec rag-agent-dev /bin/bash
# Or: make docker-dev-shell

# Clean up everything
docker-compose -f docker-compose.dev.yml down -v
# Or: make docker-dev-clean

# Complete development setup
make docker-dev-setup
```

### Production Mode Commands

```bash
# Start services
docker-compose up -d
# Or: make docker-up

# Stop services
docker-compose down
# Or: make docker-down

# View logs
docker-compose logs -f
# Or: make docker-logs

# View specific service logs
docker-compose logs -f rag-agent
# Or: make docker-logs-app

docker-compose logs -f ollama
# Or: make docker-logs-ollama

# Restart services
docker-compose restart
# Or: make docker-restart

# Access shell in container
docker-compose exec rag-agent /bin/bash
# Or: make docker-shell

docker-compose exec ollama /bin/bash
# Or: make docker-shell-ollama

# Run ingestion
docker-compose exec rag-agent python scripts/ingest.py
# Or: make docker-ingest

# View container stats
docker stats rag-agent-app rag-ollama
# Or: make docker-stats

# Complete production setup
make docker-setup
```

### Common Tasks

#### 1. Working on Code (Development)

```bash
# Start dev environment
make docker-dev

# Edit code in your editor - changes auto-reload!
# No need to rebuild or restart

# View logs to see changes
make docker-dev-logs
```

#### 2. Testing Changes

```bash
# Start dev environment
make docker-dev-up

# Run tests inside container
docker-compose -f docker-compose.dev.yml exec rag-agent-dev pytest

# Or run ingestion
docker-compose -f docker-compose.dev.yml exec rag-agent-dev python scripts/ingest.py
```

#### 3. Deploying to Production

```bash
# Build production images
make docker-build

# Start production stack
make docker-up

# Check logs
make docker-logs

# Monitor resources
make docker-stats
```

#### 4. Switching Between Modes

```bash
# Stop development
make docker-dev-down

# Start production
make docker-up

# Or vice versa
make docker-down
make docker-dev-up
```

## 📂 Volume Mounts

The Docker setup uses the following volume mounts:

```yaml
volumes:
  - ./data:/app/data              # Document directory
  - ./chroma_db:/app/chroma_db    # Vector store persistence
  - ./logs:/app/logs              # Application logs
  - ./.env:/app/.env              # Environment configuration
  - ollama_data:/root/.ollama     # Ollama models (Docker volume)
```

**Benefits:**
- Documents persist on host
- Vector store survives container restarts
- Easy access to logs
- Models persist across rebuilds

## 🎮 GPU Support

### With NVIDIA GPU

The docker-compose.yml includes GPU support for faster inference:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

**Prerequisites:**
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Without GPU

If you don't have a GPU, remove the `deploy` section from the `ollama` service in `docker-compose.yml`:

```yaml
# Comment out or remove these lines:
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: all
#           capabilities: [gpu]
```

## 🔧 Configuration

### Environment Variables

Configure the application by editing `.env`:

```bash
# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Ollama (container networking)
OLLAMA_BASE_URL=http://ollama:11434

# Models
EMBEDDING_MODEL=nomic-embed-text
CHAT_MODEL=llama3.1:8b-instruct-q4_K_M

# Optional: External providers
ANTHROPIC_API_KEY=your-key
GOOGLE_API_KEY=your-key
```

### Custom Configuration

Edit `docker-compose.yml` to customize:

```yaml
services:
  rag-agent:
    environment:
      - RETRIEVAL_K=5
      - CHUNK_SIZE=1024
      - LOG_LEVEL=DEBUG
```

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f rag-agent
docker-compose logs -f ollama

# Last 100 lines
docker-compose logs --tail=100 rag-agent
```

### Check Service Health

```bash
# Check if services are running
docker-compose ps

# Check Ollama health
curl http://localhost:11434/api/tags

# Check app health (if API enabled)
curl http://localhost:8000/health
```

### Resource Usage

```bash
# Real-time stats
docker stats rag-agent-app rag-ollama

# Or using Make
make docker-stats
```

## 🔄 Updates and Maintenance

### Update Application Code

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Update Models

```bash
# Pull latest models
docker-compose exec ollama ollama pull nomic-embed-text
docker-compose exec ollama ollama pull llama3.1:8b-instruct-q4_K_M

# Restart application
docker-compose restart rag-agent
```

### Backup Data

```bash
# Backup vector store
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Backup Ollama models (from volume)
docker run --rm -v rag_ollama_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/ollama_backup_$(date +%Y%m%d).tar.gz /data
```

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Complete cleanup
make docker-clean
```

## 🚀 Production Deployment

### Recommended Production Setup

1. **Use a reverse proxy** (nginx/Traefik) for SSL/TLS
2. **Set resource limits** in docker-compose.yml:

```yaml
services:
  rag-agent:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

3. **Enable log rotation**:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

4. **Use Docker secrets** for API keys instead of .env file
5. **Implement monitoring** (Prometheus, Grafana)
6. **Set up automated backups** for vector store

### Production docker-compose.yml Example

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    restart: always
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  rag-agent:
    build: .
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check if ports are in use
lsof -i :11434
lsof -i :8000

# Restart services
docker-compose restart
```

### Models Not Loading

```bash
# Check Ollama service
docker-compose exec ollama ollama list

# Manually pull models
docker-compose exec ollama ollama pull nomic-embed-text

# Check Ollama logs
docker-compose logs ollama
```

### Out of Memory

```bash
# Check resource usage
docker stats

# Increase memory limits in docker-compose.yml
# Or allocate more RAM to Docker Desktop
```

### Permission Issues

```bash
# Fix volume permissions
sudo chown -R $USER:$USER data/ chroma_db/ logs/

# Or run with specific user
docker-compose exec -u root rag-agent chown -R app:app /app
```

## 📝 Docker Architecture

```
┌─────────────────────────────────────────┐
│          Docker Compose Stack           │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌───────────────┐  │
│  │   Ollama    │◄───┤   RAG Agent   │  │
│  │   Service   │    │  Application  │  │
│  │             │    │               │  │
│  │ Port: 11434 │    │  Port: 8000   │  │
│  └──────┬──────┘    └───────┬───────┘  │
│         │                   │          │
│         │                   │          │
│  ┌──────▼──────┐    ┌───────▼───────┐  │
│  │   Ollama    │    │  ChromaDB     │  │
│  │   Models    │    │  Vector Store │  │
│  │  (Volume)   │    │  (Host Mount) │  │
│  └─────────────┘    └───────────────┘  │
│                                         │
└─────────────────────────────────────────┘
         │                   │
         │                   │
    Host Network        Host Filesystem
```

## 🎯 Next Steps

After deployment:

1. ✅ Verify services are running: `docker-compose ps`
2. ✅ Check logs: `make docker-logs`
3. ✅ Place documents in `./data`
4. ✅ Run ingestion: `make docker-ingest`
5. ✅ Start using the application!

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

## 🌐 FastAPI REST API

The application now includes a REST API for programmatic access.

### Starting the API Server

```bash
# Start the API server
python run_api.py

# Or with uvicorn directly
uvicorn app.api.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

### API Endpoints

#### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

#### Get Statistics
```bash
GET /stats
```

Response:
```json
{
  "app_name": "RAG Agent",
  "version": "1.0.0",
  "environment": "development",
  "vector_store": {
    "status": "ready",
    "count": 100,
    "collection": "adk_local_rag"
  },
  "models": {
    "embedding": "nomic-embed-text",
    "chat": "llama3.1:8b-instruct-q4_K_M"
  }
}
```

#### Create Session
```bash
POST /sessions
Content-Type: application/json

{
  "user_id": "my_user"  // optional, defaults to "api_user"
}
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "my_user"
}
```

#### Chat
```bash
POST /chat
Content-Type: application/json

{
  "message": "What is machine learning?",
  "user_id": "my_user",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Response:
```json
{
  "response": "Machine learning is a subset of artificial intelligence...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Example Usage with Python

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Check health
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Create a session
response = requests.post(f"{BASE_URL}/sessions", json={"user_id": "test_user"})
session_data = response.json()
session_id = session_data["session_id"]

# Send a message
response = requests.post(f"{BASE_URL}/chat", json={
    "message": "What is Python?",
    "user_id": "test_user",
    "session_id": session_id
})
print(response.json()["response"])
```

### Example Usage with cURL

```bash
# Health check
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is AI?",
    "user_id": "test_user",
    "session_id": "YOUR_SESSION_ID"
  }'
```

### Running Tests

```bash
# Run API tests
pytest tests/test_api.py -v

# Run all tests
pytest tests/ -v
```

### CORS Configuration

By default, CORS is enabled for all origins. For production, configure appropriately in `app/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Security Considerations

For production deployment:
1. **Add authentication** (JWT, API keys, OAuth2)
2. **Configure CORS** to specific origins
3. **Add rate limiting** to prevent abuse
4. **Use HTTPS** with proper TLS certificates
5. **Validate and sanitize** all inputs
6. **Implement logging** for security events


# Multi-Provider RAG Support

The ADK RAG agent now supports multiple LLM providers for enhanced flexibility and performance.

## Available Providers

### 1. **Local (Ollama)** - Default
- Fast, private, runs locally
- No API costs
- Always available

### 2. **Anthropic Claude** - Optional
- Best for complex reasoning and analysis
- Superior nuanced understanding
- Requires API key

### 3. **Google Gemini** - Optional
- Fast responses
- Excellent for factual queries and summaries
- Requires API key

## Configuration

### Step 1: Install Dependencies

```bash
pip install anthropic google-generativeai
```

### Step 2: Set API Keys

Add to your `.env` file:

```bash
# Anthropic (optional)
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Google (optional)
GOOGLE_API_KEY=your_google_key_here
GOOGLE_MODEL=gemini-2.0-flash-exp
```

### Step 3: Run the Application

```bash
python main.py
```

The application will automatically detect and enable available providers based on your API keys.

## How It Works

The ADK agent intelligently routes queries to the most appropriate provider:

- **Simple factual questions** → Local Ollama or Google Gemini (fast)
- **Complex analysis/reasoning** → Anthropic Claude (best quality)
- **Technical deep-dives** → Anthropic Claude
- **Quick summaries** → Google Gemini or Local Ollama

## Direct Provider Selection

You can also query a specific provider directly:

```python
from app.core.application import RAGAgentApp

app = RAGAgentApp()

# Use local provider
answer, sources = app.query_rag("What is X?", provider="local")

# Use Anthropic
answer, sources = app.query_rag("Analyze Y", provider="anthropic")

# Use Google
answer, sources = app.query_rag("Summarize Z", provider="google")
```

## Check Available Providers

```python
app = RAGAgentApp()
stats = app.get_stats()
print(stats['providers'])
# Output: {'local': True, 'anthropic': True, 'google': True}
```

## Cost Considerations

- **Local (Ollama)**: Free, requires local compute
- **Anthropic**: Pay per token ([pricing](https://www.anthropic.com/pricing))
- **Google**: Pay per token ([pricing](https://ai.google.dev/pricing))

The agent uses local provider by default to minimize costs, only routing to external providers when beneficial for query quality.

## 📄 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please follow the existing code structure and add tests for new features.

## 📧 Support

For issues and questions, please open a GitHub issue or contact the development team.