"""
Application configuration settings.
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


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
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "development"),
            api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
            api_timeout=int(os.getenv("API_TIMEOUT", "180")),

            # Provider
            provider_type=os.getenv("PROVIDER_TYPE", "ollama"),

            # Ollama
            embedding_model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            chat_model=os.getenv("CHAT_MODEL", "phi3:mini"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),

            # llama.cpp
            llamacpp_embedding_model_path=os.getenv("LLAMACPP_EMBEDDING_MODEL_PATH"),
            llamacpp_chat_model_path=os.getenv("LLAMACPP_CHAT_MODEL_PATH"),
            llamacpp_n_ctx=int(os.getenv("LLAMACPP_N_CTX", "2048")),
            llamacpp_n_batch=int(os.getenv("LLAMACPP_N_BATCH", "512")),
            llamacpp_n_threads=int(os.getenv("LLAMACPP_N_THREADS")) if os.getenv("LLAMACPP_N_THREADS") else None,
            llamacpp_temperature=float(os.getenv("LLAMACPP_TEMPERATURE", "0.7")),
            llamacpp_max_tokens=int(os.getenv("LLAMACPP_MAX_TOKENS", "512")),

            # Other settings
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_to_file=os.getenv("LOG_TO_FILE", "false").lower() == "true",
            retrieval_k=int(os.getenv("RETRIEVAL_K", "3")),
            chroma_hnsw_construction_ef=int(os.getenv("CHROMA_HNSW_CONSTRUCTION_EF", "100")),
            chroma_hnsw_search_ef=int(os.getenv("CHROMA_HNSW_SEARCH_EF", "50")),
        )


# Global settings instance
settings = Settings.from_env()