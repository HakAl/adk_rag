"""
Run the FastAPI application in production mode.
"""
import uvicorn
import os
import sys

# Add error handling for imports
try:
    from config import settings

    print(f"✓ Config loaded successfully")
    print(f"  Environment: {getattr(settings, 'environment', 'unknown')}")
    print(f"  Debug: {getattr(settings, 'debug', 'unknown')}")
except Exception as e:
    print(f"✗ Failed to load config: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

try:
    from app.api.main import app

    print(f"✓ App imported successfully")
except Exception as e:
    print(f"✗ Failed to import app: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on 0.0.0.0:{port}")

    uvicorn.run(
        app,  # Use the app object directly instead of string
        host="0.0.0.0",
        port=port,
        log_level="info",
        # Critical for streaming - disable keep-alive timeout
        timeout_keep_alive=0,
        # Use smaller buffer for immediate flushing
        limit_concurrency=None,
        # Ensure we're using HTTP/1.1 with proper chunked transfer
        http="h11"
    )