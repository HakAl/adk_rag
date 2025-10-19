"""
Start llama-server on Windows for ADK tool calling support.
Supports dual model setup: Phi-3 (fast) and Mistral-7B (smart).
Uses .env configuration for consistency with main application.
"""
import subprocess
import sys
import os
import time
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


def get_optional_env(var_name: str, default: str = None) -> str:
    """Get optional environment variable with default."""
    return os.getenv(var_name, default)


# Required paths
LLAMA_SERVER_PATH = get_required_env("LLAMA_SERVER_PATH")
MODELS_BASE_DIR = get_required_env("MODELS_BASE_DIR")

# Phi-3 (Fast) Model Configuration
PHI3_MODEL_PATH_CONTAINER = get_required_env("LLAMACPP_CHAT_MODEL_PATH")
PHI3_MODEL_PATH = os.path.join(MODELS_BASE_DIR, PHI3_MODEL_PATH_CONTAINER.lstrip('/').replace('/', '\\'))
PHI3_PORT = int(get_required_env("LLAMA_SERVER_PORT"))

# Mistral-7B (Smart) Model Configuration - Optional for dual model setup
MISTRAL_MODEL_PATH_CONTAINER = get_optional_env("LLAMACPP_MISTRAL_MODEL_PATH")
MISTRAL_PORT = int(get_optional_env("LLAMA_SERVER_MISTRAL_PORT", "8081"))

if MISTRAL_MODEL_PATH_CONTAINER:
    MISTRAL_MODEL_PATH = os.path.join(MODELS_BASE_DIR, MISTRAL_MODEL_PATH_CONTAINER.lstrip('/').replace('/', '\\'))
else:
    MISTRAL_MODEL_PATH = None

# Server configuration
HOST = get_required_env("LLAMA_SERVER_HOST")
CONTEXT_SIZE = int(get_required_env("LLAMACPP_N_CTX"))
THREADS = int(get_required_env("LLAMACPP_N_THREADS"))

# ============================================
# END CONFIGURATION
# ============================================


def check_model_exists(model_path: str, model_name: str) -> bool:
    """Check if the model file exists."""
    if not os.path.exists(model_path):
        print(f"❌ Error: {model_name} model file not found at: {model_path}")
        print(f"\nUsing base directory: {MODELS_BASE_DIR}")
        print("\nPlease verify:")
        print("1. MODELS_BASE_DIR points to your models directory")
        print(f"2. Model path is correct in .env file")
        return False
    return True


def check_server_exists() -> bool:
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


def check_server_health(port: int) -> bool:
    """Check if server is already running on given port."""
    try:
        import requests
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass
    return False


def start_server(model_path: str, port: int, model_name: str):
    """Start a llama-server process."""

    print(f"\n{'=' * 60}")
    print(f"Starting llama-server: {model_name}")
    print(f"{'=' * 60}")
    print(f"Model Path:  {model_path}")
    print(f"Port:        {port}")
    print(f"Host:        {HOST}")
    print(f"Context:     {CONTEXT_SIZE}")
    print(f"Threads:     {THREADS}")
    print(f"Tool Support: ENABLED (--jinja flag)")
    print(f"{'=' * 60}\n")

    # Build command
    cmd = [
        LLAMA_SERVER_PATH,
        "-m", model_path,
        "--port", str(port),
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
            bufsize=1,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )

        return process

    except FileNotFoundError:
        print(f"❌ Error: Could not find executable at: {LLAMA_SERVER_PATH}")
        return None

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None


def stream_output(process, model_name: str):
    """Stream output from a process."""
    try:
        for line in process.stdout:
            print(f"[{model_name}] {line}", end='')
    except:
        pass


def main():
    """Main function to start llama-server(s)."""

    print("\nllama-server Startup Script for Windows")
    print("Configuration loaded from .env file")
    print("-" * 60)

    # Check server executable exists
    if not check_server_exists():
        sys.exit(1)

    # Determine if running dual model setup
    dual_mode = MISTRAL_MODEL_PATH is not None

    if dual_mode:
        print("\n🔄 DUAL MODEL MODE DETECTED")
        print(f"  Fast Model (Phi-3):     Port {PHI3_PORT}")
        print(f"  Smart Model (Mistral):  Port {MISTRAL_PORT}")
    else:
        print("\n⚡ SINGLE MODEL MODE")
        print(f"  Model (Phi-3):          Port {PHI3_PORT}")
        print("\n💡 Tip: Set LLAMACPP_MISTRAL_MODEL_PATH in .env for dual model support")

    # Check if servers are already running
    phi3_running = check_server_health(PHI3_PORT)
    mistral_running = check_server_health(MISTRAL_PORT) if dual_mode else False

    if phi3_running:
        print(f"\n✅ Phi-3 server already running on port {PHI3_PORT}")
    if mistral_running:
        print(f"✅ Mistral server already running on port {MISTRAL_PORT}")

    if phi3_running and (not dual_mode or mistral_running):
        print("\nAll required servers are already running.")
        print("Stop them first if you want to restart.")
        sys.exit(0)

    # Verify model files exist
    if not phi3_running and not check_model_exists(PHI3_MODEL_PATH, "Phi-3"):
        sys.exit(1)

    if dual_mode and not mistral_running and not check_model_exists(MISTRAL_MODEL_PATH, "Mistral-7B"):
        sys.exit(1)

    # Start servers
    processes = []

    try:
        # Start Phi-3 server
        if not phi3_running:
            print("\n🚀 Starting Phi-3 server (fast model)...")
            phi3_process = start_server(PHI3_MODEL_PATH, PHI3_PORT, "Phi-3")
            if phi3_process:
                processes.append(("Phi-3", phi3_process))
                time.sleep(2)  # Give it time to start
            else:
                print("❌ Failed to start Phi-3 server")
                sys.exit(1)

        # Start Mistral server if dual mode
        if dual_mode and not mistral_running:
            print("\n🎯 Starting Mistral-7B server (smart model)...")
            mistral_process = start_server(MISTRAL_MODEL_PATH, MISTRAL_PORT, "Mistral-7B")
            if mistral_process:
                processes.append(("Mistral-7B", mistral_process))
                time.sleep(2)  # Give it time to start
            else:
                print("❌ Failed to start Mistral-7B server")
                # Stop Phi-3 if it was just started
                if not phi3_running:
                    processes[0][1].terminate()
                sys.exit(1)

        print("\n" + "=" * 60)
        print("✅ All servers started successfully!")
        print("=" * 60)
        if not phi3_running:
            print(f"  Phi-3:     http://localhost:{PHI3_PORT}")
        if dual_mode and not mistral_running:
            print(f"  Mistral:   http://localhost:{MISTRAL_PORT}")
        print("\nPress Ctrl+C to stop all servers")
        print("=" * 60 + "\n")

        # Wait for processes and stream output
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\n❌ {name} server stopped unexpectedly")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping llama-server(s)...")
        for name, process in processes:
            try:
                process.terminate()
                print(f"  Stopping {name}...")
                process.wait(timeout=5)
            except:
                process.kill()
        print("✅ All servers stopped")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        for name, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        sys.exit(1)


if __name__ == "__main__":
    main()