"""
Application configuration settings.
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Settings:
    """Application settings."""

    # Application
    app_name: str = "VIBE Agent"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # API Configuration
    api_base_url: str = "http://localhost:8000"
    api_timeout: int = 180  # 3 minutes for agent processing

    # Database Configuration
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_agent"
    database_echo: bool = False

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(init=False)
    vector_store_dir: Path = field(init=False)
    log_dir: Path = field(init=False)

    # Vector Store
    collection_name: str = "adk_local_rag"
    chunk_size: int = 1024
    chunk_overlap: int = 100
    retrieval_k: int = 3

    # ChromaDB Performance Settings
    chroma_hnsw_space: str = "cosine"
    chroma_hnsw_construction_ef: int = 100
    chroma_hnsw_search_ef: int = 50
    chroma_hnsw_m: int = 16

    # Provider Configuration
    provider_type: str = "ollama"  # 'ollama' or 'llamacpp'

    # Ollama Configuration
    embedding_model: str = "nomic-embed-text"
    chat_model: str = "phi3:mini"
    ollama_base_url: str = "http://localhost:11434"

    # llama.cpp Configuration
    llamacpp_embedding_model_path: Optional[str] = None
    llamacpp_chat_model_path: Optional[str] = None
    llamacpp_n_ctx: int = 2048
    llamacpp_n_batch: int = 512
    llamacpp_n_threads: Optional[int] = None
    llamacpp_temperature: float = 0.7
    llamacpp_max_tokens: int = 512

    # llama-server Configuration (Dual Model Support)
    llama_server_host: str = "127.0.0.1"
    llama_server_port: int = 8080  # Fast model (Phi-3)
    llama_server_mistral_port: int = 8081  # Smart model (Mistral-7B)

    # Cloud Provider Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    google_api_key: Optional[str] = None
    google_model: str = "gemini-2.0-flash-exp"

    # Specialist Fallback Configuration
    cloud_retry_attempts: int = 3
    enable_local_fallback: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: int = 60  # seconds

    # Router Configuration (Optional - if not set, router is disabled)
    router_model_path: Optional[str] = None
    router_n_ctx: int = 2048
    router_n_batch: int = 512
    router_n_threads: Optional[int] = None
    router_temperature: float = 0.1  # Lower for deterministic routing
    router_max_tokens: int = 256

    # Coordinator Agent Configuration
    use_coordinator_agent: bool = False  # Feature flag - disabled by default

    # Session Management
    session_timeout_minutes: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_file: bool = False

    def __post_init__(self):
        """Initialize computed paths and ensure directories exist."""
        self.data_dir = self.base_dir / "data"
        self.vector_store_dir = self.base_dir / "chroma_db"
        self.log_dir = self.base_dir / "logs"

        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        if self.log_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> 'Settings':
        """Create settings from environment variables."""
        # Get models base directory
        models_base_dir = Path(os.getenv("MODELS_BASE_DIR", "./models"))

        # Get relative paths and join with base directory
        llamacpp_embedding_path = os.getenv("LLAMACPP_EMBEDDING_MODEL_PATH")
        llamacpp_chat_path = os.getenv("LLAMACPP_CHAT_MODEL_PATH")
        router_model_path = os.getenv("ROUTER_MODEL_PATH")

        # Join with base directory if paths are provided
        if llamacpp_embedding_path:
            llamacpp_embedding_path = str(models_base_dir / llamacpp_embedding_path)
        if llamacpp_chat_path:
            llamacpp_chat_path = str(models_base_dir / llamacpp_chat_path)
        if router_model_path:
            router_model_path = str(models_base_dir / router_model_path)

        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "development"),
            api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
            api_timeout=int(os.getenv("API_TIMEOUT", "180")),

            # Database
            database_url=os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_agent"),
            database_echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",

            # Provider
            provider_type=os.getenv("PROVIDER_TYPE", "ollama"),

            # Ollama
            embedding_model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            chat_model=os.getenv("CHAT_MODEL", "phi3:mini"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),

            # llama.cpp - now using full paths
            llamacpp_embedding_model_path=llamacpp_embedding_path,
            llamacpp_chat_model_path=llamacpp_chat_path,
            llamacpp_n_ctx=int(os.getenv("LLAMACPP_N_CTX", "2048")),
            llamacpp_n_batch=int(os.getenv("LLAMACPP_N_BATCH", "512")),
            llamacpp_n_threads=int(os.getenv("LLAMACPP_N_THREADS")) if os.getenv("LLAMACPP_N_THREADS") else None,
            llamacpp_temperature=float(os.getenv("LLAMACPP_TEMPERATURE", "0.7")),
            llamacpp_max_tokens=int(os.getenv("LLAMACPP_MAX_TOKENS", "512")),

            # llama-server (Dual Model Support)
            llama_server_host=os.getenv("LLAMA_SERVER_HOST", "127.0.0.1"),
            llama_server_port=int(os.getenv("LLAMA_SERVER_PORT", "8080")),
            llama_server_mistral_port=int(os.getenv("LLAMA_SERVER_MISTRAL_PORT", "8081")),

            # Cloud Providers
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            google_model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-exp"),

            # Specialist Fallback
            cloud_retry_attempts=int(os.getenv("CLOUD_RETRY_ATTEMPTS", "3")),
            enable_local_fallback=os.getenv("ENABLE_LOCAL_FALLBACK", "true").lower() == "true",
            circuit_breaker_failure_threshold=int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")),
            circuit_breaker_timeout=int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60")),

            # Router (Optional)
            router_model_path=router_model_path,
            router_n_ctx=int(os.getenv("ROUTER_N_CTX", "2048")),
            router_n_batch=int(os.getenv("ROUTER_N_BATCH", "512")),
            router_n_threads=int(os.getenv("ROUTER_N_THREADS")) if os.getenv("ROUTER_N_THREADS") else None,
            router_temperature=float(os.getenv("ROUTER_TEMPERATURE", "0.1")),
            router_max_tokens=int(os.getenv("ROUTER_MAX_TOKENS", "256")),

            # Coordinator Agent
            use_coordinator_agent=os.getenv("USE_COORDINATOR_AGENT", "false").lower() == "true",

            # Other settings
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_to_file=os.getenv("LOG_TO_FILE", "false").lower() == "true",
            retrieval_k=int(os.getenv("RETRIEVAL_K", "3")),
            chroma_hnsw_construction_ef=int(os.getenv("CHROMA_HNSW_CONSTRUCTION_EF", "100")),
            chroma_hnsw_search_ef=int(os.getenv("CHROMA_HNSW_SEARCH_EF", "50")),
        )


# Global settings instance
settings = Settings.from_env()