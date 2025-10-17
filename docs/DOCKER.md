# Docker Deployment Guide

Complete guide for running VIBE Agent in Docker containers.

## Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose V2
- (Optional) NVIDIA Docker runtime for GPU support

### Basic Setup

```bash
# 1. Configure environment
cp .env.docker .env
# Edit .env as needed

# 2. Start services
docker-compose up -d

# 3. Pull models (first time)
make docker-pull-models

# 4. Ingest documents
cp your-docs/* data/
make docker-ingest
```

## Development vs Production

### Development Mode

**Best for:** Local development with hot reload

```bash
# Start with live code updates
make docker-dev

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
# Start optimized stack
make docker-up

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
make docker-up              # Start production
make docker-down            # Stop production
make docker-dev             # Start development
make docker-dev-down        # Stop development

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
curl http://localhost:11434/api/tags    # Ollama
curl http://localhost:8000/health       # App API
```

## Volume Mounts

The stack uses these volume mounts:

```yaml
./data           → /app/data              # Documents
./chroma_db      → /app/chroma_db         # Vector store
./logs           → /app/logs              # Logs
./.env           → /app/.env              # Config
ollama_data      → /root/.ollama          # Models (Docker volume)
```

## GPU Support

### With NVIDIA GPU

The default `docker-compose.yml` includes GPU support:

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

### Without GPU

Remove the `deploy` section from the `ollama` service:

```yaml
# Comment out in docker-compose.yml:
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
```

## Configuration

### Environment Variables

Edit `.env` file:

```bash
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

```bash
docker-compose exec ollama ollama pull nomic-embed-text
docker-compose restart rag-agent
```

### Backup Data

```bash
# Vector store
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Ollama models (from volume)
docker run --rm -v rag_ollama_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/ollama_backup_$(date +%Y%m%d).tar.gz /data
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
lsof -i :11434
lsof -i :8000

# Restart
docker-compose restart
```

### Models Not Loading

```bash
# Check Ollama
docker-compose exec ollama ollama list

# Pull manually
docker-compose exec ollama ollama pull nomic-embed-text

# Check logs
docker-compose logs ollama
```

### Out of Memory

```bash
# Check usage
docker stats

# Increase limits in docker-compose.yml
# Or allocate more RAM to Docker Desktop
```

### Permission Issues

```bash
# Fix volume permissions
sudo chown -R $USER:$USER data/ chroma_db/ logs/

# Or run as root
docker-compose exec -u root rag-agent chown -R app:app /app
```

## Architecture

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