"""
Run the FastAPI application with streaming optimizations.
"""
import uvicorn
from config import settings


if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        # Critical for streaming - disable keep-alive timeout
        timeout_keep_alive=0,
        # Use smaller buffer for immediate flushing
        limit_concurrency=None,
        # Ensure we're using HTTP/1.1 with proper chunked transfer
        http="h11"
    )