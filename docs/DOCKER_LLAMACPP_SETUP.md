# llama.cpp Docker Setup Guide

This guide explains how to run the RAG Agent with llama.cpp models in Docker.

## Prerequisites

1. Docker and Docker Compose installed
2. GGUF model files downloaded
3. At least 4GB free disk space for models

## Directory Structure

Create the following directory structure in your project root:

```
./models/
├── embeddings/
│   └── nomic-embed-text-q4_k_m.gguf
└── chat/
    └── phi3-mini-4k-instruct-q4_k_m.gguf
```

## Step 1: Download Model Files

Download GGUF models from Hugging Face:

```bash
# Create directories
mkdir -p models/embeddings models/chat

# Download embedding model (example)
wget -O models/embeddings/nomic-embed-text-q4_k_m.gguf \
  https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf

# Download chat model (example)
wget -O models/chat/phi3-mini-4k-instruct-q4_k_m.gguf \
  https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
```

**Note:** Replace URLs with actual model locations. Check Hugging Face for quantized GGUF versions.

## Step 2: Configure Environment

Update your `.env` file:

```bash
# Set provider to llamacpp
PROVIDER_TYPE=llamacpp

# Configure model paths (these are container paths)
LLAMACPP_EMBEDDING_MODEL_PATH=/app/models/embeddings/nomic-embed-text-q4_k_m.gguf
LLAMACPP_CHAT_MODEL_PATH=/app/models/chat/phi3-mini-4k-instruct-q4_k_m.gguf

# Optional: Adjust performance settings
LLAMACPP_N_CTX=2048
LLAMACPP_N_BATCH=512
LLAMACPP_N_THREADS=4
LLAMACPP_TEMPERATURE=0.7
LLAMACPP_MAX_TOKENS=512
```

## Step 3: Build Docker Image

Build the image with llama.cpp support:

```bash
# Production
make docker-build-llamacpp

# Development
make docker-dev-build-llamacpp
```

This will:
- Install llama-cpp-python with CPU support
- Add ~500MB to the image size
- Take 5-10 minutes to build (llama.cpp compilation)

## Step 4: Start Services

```bash
# Production
make docker-up-llamacpp

# Development
make docker-dev-up-llamacpp
```

The startup process will:
1. Validate model directories exist
2. Start only the rag-agent container (no Ollama needed)
3. Mount your local `./models` directory

## Step 5: Verify Setup

Check logs to ensure models loaded successfully:

```bash
# View logs
make docker-logs-app

# Expected output:
# Loading embedding model from /app/models/embeddings/nomic-embed-text-q4_k_m.gguf
# Loading chat model from /app/models/chat/phi3-mini-4k-instruct-q4_k_m.gguf
# ✅ Models loaded successfully
```

## Troubleshooting

### Model Files Not Found

**Error:** `FileNotFoundError: /app/models/embeddings/...`

**Solution:**
```bash
# Check if files exist locally
ls -lh models/embeddings/
ls -lh models/chat/

# Verify paths in .env match actual filenames
cat .env | grep LLAMACPP
```

### Build Fails During llama-cpp-python Installation

**Error:** `error: command 'gcc' failed`

**Solution:** This shouldn't happen with the Dockerfile, but if it does:
```bash
# Clean and rebuild
make docker-clean
make docker-build-llamacpp
```

### Out of Memory

**Error:** Container crashes or becomes unresponsive

**Solution:** Reduce model size or adjust settings:
```bash
# Use smaller quantized models (Q4_K_M instead of Q8_0)
# Or adjust context size in .env:
LLAMACPP_N_CTX=1024
LLAMACPP_N_BATCH=256
```

## Switching Between Providers

### Switch from Ollama to llama.cpp

```bash
# 1. Stop current services
make docker-down

# 2. Update .env
echo "PROVIDER_TYPE=llamacpp" >> .env

# 3. Rebuild and start
make docker-build-llamacpp
make docker-up-llamacpp
```

### Switch from llama.cpp to Ollama

```bash
# 1. Stop current services
make docker-down

# 2. Update .env
echo "PROVIDER_TYPE=ollama" >> .env

# 3. Start with Ollama
make docker-build
make docker-up-ollama
```

## Performance Tuning

### CPU Optimization

```bash
# Set threads to match your CPU cores
LLAMACPP_N_THREADS=8

# Larger batch size for better throughput
LLAMACPP_N_BATCH=1024
```

### Memory Optimization

```bash
# Reduce context window
LLAMACPP_N_CTX=1024

# Smaller batch size
LLAMACPP_N_BATCH=256
```

## Model Recommendations

### Small Models (2-4GB RAM)
- **Embedding:** `nomic-embed-text-v1.5.Q4_K_M.gguf` (~250MB)
- **Chat:** `phi-3-mini-4k-instruct.Q4_K_M.gguf` (~2.5GB)

### Medium Models (4-8GB RAM)
- **Embedding:** `nomic-embed-text-v1.5.Q8_0.gguf` (~500MB)
- **Chat:** `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (~4GB)

### Quantization Guide
- **Q4_K_M:** Best balance (recommended)
- **Q5_K_M:** Better quality, 25% larger
- **Q8_0:** Highest quality, 2x larger
- **Q3_K_M:** Smallest, lower quality

## Development Workflow

### Hot Reload with llama.cpp

Development mode supports hot reload:

```bash
# Start dev environment
make docker-dev-up-llamacpp

# Edit code in ./app/
# Changes auto-reload without restart

# View logs
make docker-dev-logs
```

### Testing in Container

```bash
# Run tests
docker-compose -f docker-compose.dev.yml exec rag-agent-dev pytest

# Interactive shell
make docker-dev-shell

# Inside container:
python
>>> from llama_cpp import Llama
>>> # Test model loading
```

## Cleanup

```bash
# Remove containers and volumes
make docker-clean

# Remove images
docker image rm rag-agent-app

# Keep model files (in ./models/)
```

## Size Comparison

| Configuration | Image Size | Build Time |
|--------------|------------|------------|
| Ollama only | ~1.0GB | 2-3 min |
| llama.cpp only | ~1.5GB | 8-12 min |

## FAQ

**Q: Can I use both Ollama and llama.cpp simultaneously?**
A: No, choose one at build time with `PROVIDER_TYPE`. To use both, build two separate images.

**Q: Do I need the Ollama container when using llama.cpp?**
A: No, the Ollama service is disabled (via profiles) when using llama.cpp.

**Q: Can I use GPU with llama.cpp in Docker?**
A: Yes, but requires additional setup:
```dockerfile
# Add to Dockerfile builder stage:
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
pip install llama-cpp-python
```

**Q: Where can I find more GGUF models?**
A: Check Hugging Face:
- https://huggingface.co/models?library=gguf
- Search for "gguf" + model name

## Next Steps

- Read `README.md` for general usage
- Check `docs/CONFIGURATION.md` for advanced settings
- See `docs/PERFORMANCE.md` for optimization tips