# Docker Setup Instructions

## Usage

### Development Mode

```bash
# Cloud providers only (no local models)
docker-compose -f docker-compose.dev.yml up

# With Ollama
docker-compose -f docker-compose.dev.yml --profile ollama up

# With llama.cpp
docker-compose -f docker-compose.dev.yml --profile llamacpp up

# Access:
# - Frontend: http://localhost:3000 (hot reload enabled)
# - Backend API: http://localhost:8000
# - PostgreSQL: localhost:5432
```

### Production Mode

```bash
# Build and start (cloud providers only)
docker-compose up -d --build

# With Ollama
docker-compose --profile ollama up -d --build

# With llama.cpp
docker-compose --profile llamacpp up -d --build

# Access:
# - Application: http://localhost:8080 (nginx serves frontend + proxies API)
# - Backend API: http://localhost:8000 (direct access)
```

## Important Notes

### 1. Frontend Vite Configuration
Update your `frontend/vite.config.ts` for Docker:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Required for Docker
    port: 3000,
    proxy: {
      '/sessions': {
        target: 'http://rag-agent-dev:8000', // Changed from localhost
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://rag-agent-dev:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://rag-agent-dev:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://rag-agent-dev:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### 2. Database Initialization

The database schema is created automatically via `database.py:init_db()`. Ensure your FastAPI app calls this on startup:

```python
# In your FastAPI app startup
from database import init_db

@app.on_event("startup")
async def startup_event():
    await init_db()
```

### 3. Model Files

Mount your local model directory:
- Development: `./models` → `/app/models` (read-only)
- llama-server: `./models` → `/models` (read-only)

Expected structure:
```
models/
├── chat/
│   ├── phi3-mini-4k-instruct-q4_k_m.gguf
│   └── mistral-7b-instruct-v0.2.Q4_K_M.gguf (optional)
└── embeddings/
    └── nomic-embed-text-v1.5-q4_k_m.gguf
```

### 4. Environment Variables

The `.env` file is mounted into containers. Key differences:

**Development:**
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres-dev:5432/rag_agent`
- `OLLAMA_BASE_URL=http://ollama:11434`
- `LLAMA_SERVER_HOST=llama-server-dev`

**Production:**
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/rag_agent`
- Same Ollama/llama URLs

### 5. Streaming Support

The nginx configuration includes critical settings for SSE streaming:
- `proxy_buffering off` - Prevents response buffering
- `proxy_cache off` - Disables caching
- `chunked_transfer_encoding on` - Enables chunked responses
- `proxy_read_timeout 300s` - Long timeout for streams

**Your streaming endpoints will work perfectly through nginx!**

### 6. llama-server Container

Builds llama.cpp from source and starts servers based on your configuration:
- Primary model (Phi-3): Port 8080
- Secondary model (Mistral): Port 8081 (if `LLAMACPP_MISTRAL_MODEL_PATH` is set)

### 7. Health Checks

All services have health checks:
- PostgreSQL: `pg_isready`
- Backend: `curl http://localhost:8000/health`
- llama-server: `curl http://localhost:8080/health`
- Nginx: `wget http://localhost/health`

## Common Commands

```bash
# View logs
docker-compose logs -f rag-agent
docker-compose logs -f frontend-dev
docker-compose logs -f postgres

# Rebuild specific service
docker-compose up -d --build rag-agent

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes database data)
docker-compose down -v

# Execute command in container
docker-compose exec rag-agent python -c "from database import init_db; import asyncio; asyncio.run(init_db())"

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d rag_agent
```

## Troubleshooting

### Frontend can't connect to backend in dev
- Check that Vite config uses `rag-agent-dev:8000` not `localhost:8000`
- Ensure both containers are on same network

### Streaming doesn't work through nginx
- Verify nginx config has `proxy_buffering off`
- Check nginx logs: `docker-compose logs nginx`
- Test direct backend: `curl http://localhost:8000/chat/...`

### llama-server fails to start
- Verify model files exist in `./models/`
- Check paths in `.env` match actual file locations
- View logs: `docker-compose logs llama-server`

### Database connection refused
- Ensure postgres is healthy: `docker-compose ps`
- Check DATABASE_URL uses correct hostname (`postgres` or `postgres-dev`)
- Verify port 5432 not in use on host

## Migration from Old Setup

1. Backup existing data:
   ```bash
   cp -r data data.backup
   cp -r chroma_db chroma_db.backup
   ```

2. Stop old containers:
   ```bash
   docker-compose down
   ```

3. Update files with new versions

4. Start new stack:
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

5. Database will auto-initialize on first run