"""
Run the FastAPI application in production mode with extensive error checking.
"""
import sys
import os
import multiprocessing

print("=" * 60)
print("STARTUP DIAGNOSTICS")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"PORT environment variable: {os.environ.get('PORT', 'NOT SET')}")
print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT', 'NOT SET')}")
print(f"DATABASE_URL: {'SET' if os.environ.get('DATABASE_URL') else 'NOT SET'}")
print(f"PROVIDER_TYPE: {os.environ.get('PROVIDER_TYPE', 'NOT SET')}")
print(f"Available CPUs: {multiprocessing.cpu_count()}")
print("=" * 60)

# Test imports one by one
print("\n1. Testing uvicorn import...")
try:
    import uvicorn
    print("   ✓ uvicorn imported")
except Exception as e:
    print(f"   ✗ Failed to import uvicorn: {e}")
    sys.exit(1)

print("\n2. Testing config import...")
try:
    from config import settings
    print("   ✓ config imported")
    print(f"   - Environment: {getattr(settings, 'environment', 'unknown')}")
    print(f"   - Debug: {getattr(settings, 'debug', 'unknown')}")
    print(f"   - App name: {getattr(settings, 'app_name', 'unknown')}")
    print(f"   - Provider: {getattr(settings, 'provider_type', 'unknown')}")
except Exception as e:
    print(f"   ✗ Failed to import config: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing app import...")
try:
    from app.api.main import app
    print("   ✓ app imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL IMPORTS SUCCESSFUL - STARTING SERVER")
print("=" * 60 + "\n")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    # Calculate workers (max 4 for Render free tier)
    cpu_count = multiprocessing.cpu_count()
    workers = int(os.environ.get("WORKERS", min(4, (cpu_count * 2) + 1)))

    print(f"Configuration:")
    print(f"  - Host: 0.0.0.0")
    print(f"  - Port: {port}")
    print(f"  - Workers: {workers}")
    print(f"  - Timeout: 300s (5 min)")
    print("")

    try:
        if workers > 1:
            # Multi-worker mode (use string import)
            print(f"Starting uvicorn with {workers} workers (production mode)\n")
            uvicorn.run(
                "app.api.main:app",  # String import for workers
                host="0.0.0.0",
                port=port,
                workers=workers,
                log_level="info",
                timeout_keep_alive=300,  # 5 minutes for cloud API calls
                timeout_graceful_shutdown=30,
                http="h11"
            )
        else:
            # Single-worker mode (use app object)
            print("Starting uvicorn with 1 worker (development mode)\n")
            uvicorn.run(
                app,  # App object for single worker
                host="0.0.0.0",
                port=port,
                log_level="info",
                timeout_keep_alive=300,
                timeout_graceful_shutdown=30,
                http="h11"
            )
    except Exception as e:
        print(f"\n✗ Failed to start uvicorn: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)