"""
Start llama-server on Windows for ADK tool calling support.
Uses .env configuration for consistency with main application.
"""
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# CONFIGURATION FROM .ENV - REQUIRED
# ============================================

def get_required_env(var_name: str) -> str:
    """Get required environment variable or fail."""
    value = os.getenv(var_name)
    if not value:
        print(f"❌ Error: Required environment variable '{var_name}' not found in .env file")
        print(f"\nPlease add {var_name} to your .env file")
        sys.exit(1)
    return value


# Required paths
LLAMA_SERVER_PATH = get_required_env("LLAMA_SERVER_PATH")

# Convert Docker container path to Windows path
MODEL_PATH_CONTAINER = get_required_env("LLAMACPP_CHAT_MODEL_PATH")
MODELS_BASE_DIR = get_required_env("MODELS_BASE_DIR")

# Convert /chat/model.gguf to C:\...\models\chat\model.gguf
MODEL_PATH = os.path.join(MODELS_BASE_DIR, MODEL_PATH_CONTAINER.lstrip('/').replace('/', '\\'))

# Server configuration
PORT = int(get_required_env("LLAMA_SERVER_PORT"))
HOST = get_required_env("LLAMA_SERVER_HOST")
CONTEXT_SIZE = int(get_required_env("LLAMACPP_N_CTX"))
THREADS = int(get_required_env("LLAMACPP_N_THREADS"))

# ============================================
# END CONFIGURATION
# ============================================


def check_model_exists():
    """Check if the model file exists."""
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Model file not found at: {MODEL_PATH}")
        print(f"\nConverted from Docker path: {MODEL_PATH_CONTAINER}")
        print(f"Using base directory: {MODELS_BASE_DIR}")
        print("\nPlease verify:")
        print("1. MODELS_BASE_DIR points to your models directory")
        print("2. LLAMACPP_CHAT_MODEL_PATH matches your Docker container structure")
        return False
    return True


def check_server_exists():
    """Check if llama-server executable exists."""
    if not os.path.exists(LLAMA_SERVER_PATH):
        print(f"❌ Error: llama-server not found at: {LLAMA_SERVER_PATH}")
        print("\nPlease check LLAMA_SERVER_PATH in your .env file")
        print("\nOptions:")
        print("1. Update LLAMA_SERVER_PATH in your .env file")
        print("2. Build llama.cpp: https://github.com/ggerganov/llama.cpp")
        print("3. Or switch to Ollama for easier setup")
        return False
    return True


def start_llama_server():
    """Start the llama-server process."""

    # Check server executable exists
    if not check_server_exists():
        return False

    # Check model exists
    if not check_model_exists():
        return False

    print("=" * 60)
    print("Starting llama-server for ADK tool calling")
    print("=" * 60)
    print(f"Server Path: {LLAMA_SERVER_PATH}")
    print(f"Model Path:  {MODEL_PATH}")
    print(f"  (from Docker path: {MODEL_PATH_CONTAINER})")
    print(f"Port:        {PORT}")
    print(f"Host:        {HOST}")
    print(f"Context:     {CONTEXT_SIZE}")
    print(f"Threads:     {THREADS}")
    print(f"Tool Support: ENABLED (--jinja flag)")
    print("=" * 60)
    print("\nConfiguration loaded from .env file")
    print("Starting server... (Press Ctrl+C to stop)")
    print()

    # Build command with --jinja flag for tool calling support
    cmd = [
        LLAMA_SERVER_PATH,
        "-m", MODEL_PATH,
        "--port", str(PORT),
        "--host", HOST,
        "-c", str(CONTEXT_SIZE),
        "-t", str(THREADS),
        "--jinja",  # Enable tool calling support
        "--log-disable",  # Reduce log verbosity
    ]

    try:
        # Start the server process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Stream output
        for line in process.stdout:
            print(line, end='')

        process.wait()

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping llama-server...")
        process.terminate()
        process.wait()
        print("✅ Server stopped")

    except FileNotFoundError:
        print(f"❌ Error: Could not find executable at: {LLAMA_SERVER_PATH}")
        return False

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

    return True


def check_server_health():
    """Check if server is already running."""
    try:
        import requests
        response = requests.get(f"http://localhost:{PORT}/health", timeout=2)
        if response.status_code == 200:
            print(f"✅ llama-server is already running on port {PORT}")
            print(f"  Access it at: http://localhost:{PORT}")
            return True
    except:
        pass
    return False


if __name__ == "__main__":
    print("\nllama-server Startup Script for Windows")
    print("Configuration loaded from .env file")
    print("-" * 60)

    # Check if already running
    if check_server_health():
        print("\nServer is already running. Stop it first if you want to restart.")
        sys.exit(0)

    # Start the server
    success = start_llama_server()

    if not success:
        print("\n❌ Failed to start llama-server")
        print("\nTroubleshooting:")
        print("1. Make sure llama.cpp is built: cmake --build build --config Release")
        print("2. Verify these variables in your .env file:")
        print("   - LLAMA_SERVER_PATH (path to llama-server.exe)")
        print("   - MODELS_BASE_DIR (base directory where models are stored)")
        print("   - LLAMACPP_CHAT_MODEL_PATH (Docker container path, e.g., /chat/model.gguf)")
        print("   - LLAMA_SERVER_PORT")
        print("   - LLAMA_SERVER_HOST")
        print("   - LLAMACPP_N_CTX")
        print("   - LLAMACPP_N_THREADS")
        print("3. Check that your model file (.gguf) exists at the converted path")
        print("\nOr consider switching to Ollama for easier setup:")
        print("   https://ollama.com/download")
        sys.exit(1)