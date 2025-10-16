# Multi-stage build for RAG Agent Application
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create app user
RUN useradd -m -u 1000 app && \
    mkdir -p /app/data /app/chroma_db /app/logs && \
    chown -R app:app /app

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/app/.local

# Copy application code
COPY --chown=app:app . .

# Switch to app user
USER app

# Add local bin to PATH
ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Install package in editable mode
RUN pip install --user -e .

# Create volume mount points
VOLUME ["/app/data", "/app/chroma_db", "/app/logs"]

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["python", "main.py"]