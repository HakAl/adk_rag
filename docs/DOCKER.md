# Docker Deployment Guide

Complete guide for running VIBE Agent in Docker containers.

## Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose V2
- (Optional) NVIDIA Docker runtime for GPU support

### Basic Setup - Ollama (Default)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env as needed

# 2. Start services
make docker-up-ollama

# 3. Pull models (first time)
make docker-pull-models

# 4. Ingest documents
cp your-docs/* data/
make docker-ingest
```

### Alternative Setup - llama.cpp

For running with local GGUF models instead of Ollama:

```bash
# 1. Create model directories
mkdir -p models/embeddings models/chat

# 2. Download GGUF models
# Place your .gguf files in the directories above

# 3. Configure environment
cp .env.example .env
# Set PROVIDER_TYPE=llamacpp and model paths

# 4. Build and start
make docker-build-llamacpp
make docker-up-llamacpp

# 5. Ingest documents
cp your-docs/* data/
make docker-ingest
```

**See [DOCKER_LLAMACPP_SETUP.md](./DOCKER_LLAMACPP_SETUP.md) for detailed llama.cpp setup instructions.**

## Provider Selection

The application supports two providers:

| Provider | Best For | Image Size | Setup Time |
|----------|----------|------------|------------|
| **Ollama** | Easy setup, automatic model management | ~1.0GB | 2-3 min |
| **llama.cpp** | Custom models, no external service | ~1.5GB | 8-12 min |

### Switching Providers

```bash
# Switch to llama.cpp
make docker-down
# Edit .env: PROVIDER_TYPE=llamacpp
make docker-build-llamacpp
make docker-up-llamacpp

# Switch back to Ollama
make docker-down
# Edit .env: PROVIDER_TYPE=ollama
make docker-build
make docker-up-ollama
```

## Development vs Production

### Development Mode

**Best for:** Local development with hot reload

```bash
# Start with Ollama (default)
make docker-dev-up-ollama

# Or with llama.cpp
make docker-dev-build-llamacpp
make docker-dev-up-llamacpp

# Code changes auto-reload - no rebuild needed!

# View logs
make docker-dev-logs

# Stop
make docker-dev-down
```

Features:
- ✅ Hot reload enabled
- ✅ Source code mounted as volumes
- ✅ Debug logging
- ✅ Faster iteration

### Production Mode

**Best for:** Deployment and production environments

```bash
# Start optimized stack (Ollama)
make docker-up-ollama

# Or with llama.cpp
make docker-setup-llamacpp

# View logs
make docker-logs

# Stop
make docker-down
```

Features:
- ✅ Optimized performance
- ✅ Production logging
- ✅ Automatic restarts
- ✅ Resource limits
- ✅ Health checks

## Common Commands

### Service Management

```bash
# Start/stop
make docker-up-ollama       # Start with Ollama
make docker-up-llamacpp     # Start with llama.cpp
make docker-down            # Stop all services
make docker-dev-up-ollama   # Start dev with Ollama
make docker-dev-up-llamacpp # Start dev with llama.cpp
make docker-dev-down        # Stop dev services

# Build
make docker-build           # Build Ollama image
make docker-build-llamacpp  # Build llama.cpp image

# Logs
make docker-logs            # All logs
make docker-logs-app        # App logs only
make docker-logs-ollama     # Ollama logs only

# Shell access
make docker-shell           # Production shell
make docker-dev-shell       # Development shell
```

### Document Processing

```bash
# Ingest documents
make docker-ingest

# Or with options
docker-compose exec rag-agent python scripts/ingest.py --workers 8
```

### Monitoring

```bash
# View resource usage
make docker-stats

# Check service status
docker-compose ps

# Health checks
curl http://localhost:11434/api/tags    # Ollama (if using Ollama)
curl http://localhost:8000/health       # App API
```

## Volume Mounts

The stack uses these volume mounts:

### Ollama Provider
```yaml
./data           → /app/data              # Documents
./chroma_db      → /app/chroma_db         # Vector store
./logs           → /app/logs              # Logs
./.env           → /app/.env              # Config
ollama_data      → /root/.ollama          # Models (Docker volume)
```

### llama.cpp Provider
```yaml
./data           → /app/data              # Documents
./chroma_db      → /app/chroma_db         # Vector store
./logs           → /app/logs              # Logs
./models         → /app/models            # GGUF model files
./.env           → /app/.env              # Config
```

## GPU Support

### With NVIDIA GPU (Ollama)

The default `docker-compose.yml` includes GPU support for Ollama:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

**Setup NVIDIA Container Toolkit:**

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### With NVIDIA GPU (llama.cpp)

For GPU support with llama.cpp, you need to rebuild with CUDA support:

```bash
# Modify Dockerfile to include:
# ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
# Then rebuild
make docker-build-llamacpp
```

### Without GPU

Remove the `deploy` section from the `ollama` service or use llama.cpp on CPU.

## Configuration

### Environment Variables

Edit `.env` file:

**For Ollama Provider:**
```bash
# Provider Selection
PROVIDER_TYPE=ollama

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Ollama (container networking)
OLLAMA_BASE_URL=http://ollama:11434

# Models
EMBEDDING_MODEL=nomic-embed-text
CHAT_MODEL=phi3:mini

# Optional providers
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key
```

**For llama.cpp Provider:**
```bash
# Provider Selection
PROVIDER_TYPE=llamacpp

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# llama.cpp Model Paths (container paths)
LLAMACPP_EMBEDDING_MODEL_PATH=/app/models/embeddings/nomic-embed-text-q4_k_m.gguf
LLAMACPP_CHAT_MODEL_PATH=/app/models/chat/phi3-mini-4k-instruct-q4_k_m.gguf

# llama.cpp Performance Tuning
LLAMACPP_N_CTX=2048
LLAMACPP_N_BATCH=512
LLAMACPP_N_THREADS=4
LLAMACPP_TEMPERATURE=0.7
LLAMACPP_MAX_TOKENS=512
```

### Resource Limits

Edit `docker-compose.yml`:

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

## Maintenance

### Update Application

```bash
git pull
docker-compose down
docker-compose up -d --build
```

### Update Models

**Ollama:**
```bash
docker-compose exec ollama ollama pull nomic-embed-text
docker-compose restart rag-agent
```

**llama.cpp:**
```bash
# Download new GGUF files to ./models/
# Update paths in .env
docker-compose restart rag-agent
```

### Backup Data

```bash
# Vector store
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Ollama models (from volume)
docker run --rm -v rag_ollama_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/ollama_backup_$(date +%Y%m%d).tar.gz /data

# llama.cpp models
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/
```

### Clean Up

```bash
make docker-clean           # Remove everything
make docker-dev-clean       # Clean dev environment
docker-compose down -v      # Remove containers and volumes
```

## Production Recommendations

1. **Reverse Proxy**: Use nginx/Traefik for SSL/TLS
2. **Resource Limits**: Set appropriate CPU/memory limits
3. **Log Rotation**: Configure max file size and retention
4. **Secrets Management**: Use Docker secrets for API keys
5. **Monitoring**: Implement Prometheus/Grafana
6. **Backups**: Automate vector store backups
7. **Health Checks**: Configure appropriate timeouts

### Production docker-compose Example

```yaml
services:
  rag-agent:
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

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check port conflicts
lsof -i :11434  # Ollama
lsof -i :8000   # App

# Restart
docker-compose restart
```

### Models Not Loading (Ollama)

```bash
# Check Ollama
docker-compose exec ollama ollama list

# Pull manually
docker-compose exec ollama ollama pull nomic-embed-text

# Check logs
docker-compose logs ollama
```

### Models Not Loading (llama.cpp)

```bash
# Check if files exist
ls -lh models/embeddings/
ls -lh models/chat/

# Verify paths in .env
cat .env | grep LLAMACPP

# Check container logs
make docker-logs-app
```

### Out of Memory

```bash
# Check usage
docker stats

# Increase limits in docker-compose.yml
# Or allocate more RAM to Docker Desktop

# For llama.cpp, reduce context size:
# LLAMACPP_N_CTX=1024
# LLAMACPP_N_BATCH=256
```

### Permission Issues

```bash
# Fix volume permissions
sudo chown -R $USER:$USER data/ chroma_db/ logs/ models/

# Or run as root
docker-compose exec -u root rag-agent chown -R app:app /app
```

### llama.cpp Build Fails

```bash
# Clean everything
make docker-clean

# Rebuild from scratch
make docker-build-llamacpp

# Check build logs
docker-compose build rag-agent 2>&1 | tee build.log
```

## Architecture

### Ollama Architecture
```
┌─────────────────────────────────────────┐
│          Docker Compose Stack           │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌───────────────┐  │
│  │   Ollama    │◄───┤   RAG Agent   │  │
│  │   Service   │    │  Application  │  │
│  │ Port: 11434 │    │  Port: 8000   │  │
│  └──────┬──────┘    └───────┬───────┘  │
│         │                   │          │
│  ┌──────▼──────┐    ┌───────▼───────┐  │
│  │   Models    │    │  Vector Store │  │
│  │  (Volume)   │    │ (Host Mount)  │  │
│  └─────────────┘    └───────────────┘  │
└─────────────────────────────────────────┘
```

### llama.cpp Architecture
```
┌─────────────────────────────────────────┐
│          Docker Compose Stack           │
├─────────────────────────────────────────┤
│                                         │
│         ┌───────────────┐               │
│         │   RAG Agent   │               │
│         │  Application  │               │
│         │  Port: 8000   │               │
│         │ (with llama.cpp)              │
│         └───────┬───────┘               │
│                 │                       │
│    ┌────────────┼────────────┐          │
│    │            │            │          │
│  ┌─▼──────┐  ┌─▼──────┐  ┌──▼──────┐   │
│  │ Models │  │ Vector │  │  Logs   │   │
│  │ (Host) │  │ Store  │  │ (Host)  │   │
│  └────────┘  └────────┘  └─────────┘   │
└─────────────────────────────────────────┘
```

## Additional Documentation

- **llama.cpp Setup**: See [DOCKER_LLAMACPP_SETUP.md](./DOCKER_LLAMACPP_SETUP.md)
- **Quick Start**: See [QUICKSTART_LLAMACPP.md](./QUICKSTART_LLAMACPP.md)
- **Main README**: See [README.md](../README.md)