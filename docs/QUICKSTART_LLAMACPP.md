# Quick Start: llama.cpp Provider

Get up and running with llama.cpp in Docker in 5 minutes.

## Step 1: Create Model Directories (30 seconds)

```bash
mkdir -p models/embeddings models/chat
```

## Step 2: Download Models (3-5 minutes)

Download small models for testing:

```bash
# Embedding model (~250MB)
wget -O models/embeddings/nomic-embed-text-q4_k_m.gguf \
  https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf

# Chat model (~2.5GB)
wget -O models/chat/phi3-mini-q4.gguf \
  https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
```

**No wget?** Download manually from Hugging Face and place in directories.

## Step 3: Configure Environment (15 seconds)

```bash
cp .env.example .env
```

Edit `.env`:
```bash
PROVIDER_TYPE=llamacpp
LLAMACPP_EMBEDDING_MODEL_PATH=/app/models/embeddings/nomic-embed-text-q4_k_m.gguf
LLAMACPP_CHAT_MODEL_PATH=/app/models/chat/phi3-mini-q4.gguf
```

## Step 4: Build and Start (8-12 minutes)

```bash
make docker-build-llamacpp
make docker-up-llamacpp
```

## Step 5: Verify (30 seconds)

```bash
# Check logs
make docker-logs-app

# Should see:
# ✅ Models loaded successfully

# Test health endpoint
curl http://localhost:8000/health
```

## Done! 🎉

Your RAG agent is running with llama.cpp.

**Next Steps:**
- Ingest documents: `make docker-ingest`
- View full docs: `docs/DOCKER_LLAMACPP_SETUP.md`
- Try different models: Check Hugging Face for more GGUF models

## Troubleshooting

**Build takes too long?**
- This is normal for first build (compiling llama.cpp)
- Subsequent builds use cache (~2 min)

**Out of disk space?**
- Models need 3-4GB free
- Run `docker system prune` to clean up

**Models not loading?**
- Verify filenames match paths in `.env`
- Check: `ls -lh models/embeddings/ models/chat/`