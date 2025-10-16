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
    app_name: str = "RAG Agent"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(init=False)
    vector_store_dir: Path = field(init=False)
    log_dir: Path = field(init=False)
    
    # Vector Store
    collection_name: str = "adk_local_rag"
    chunk_size: int = 1024
    chunk_overlap: int = 100
    retrieval_k: int = 3  # Reduced from 5 to 3 for faster queries

    # ChromaDB Performance Settings
    chroma_hnsw_space: str = "cosine"  # Distance metric: cosine, l2, or ip
    chroma_hnsw_construction_ef: int = 100  # Reduced from default 200 for faster indexing
    chroma_hnsw_search_ef: int = 50  # Reduced from default 100 for faster search
    chroma_hnsw_m: int = 16  # Number of connections per layer (default 16)

    # Ollama Models
    embedding_model: str = "nomic-embed-text"
    chat_model: str = "llama3.1:8b-instruct-q4_K_M"
    ollama_base_url: str = "http://localhost:11434"

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
            embedding_model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            chat_model=os.getenv("CHAT_MODEL", "llama3.1:8b-instruct-q4_K_M"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_to_file=os.getenv("LOG_TO_FILE", "false").lower() == "true",
            retrieval_k=int(os.getenv("RETRIEVAL_K", "3")),
            chroma_hnsw_construction_ef=int(os.getenv("CHROMA_HNSW_CONSTRUCTION_EF", "100")),
            chroma_hnsw_search_ef=int(os.getenv("CHROMA_HNSW_SEARCH_EF", "50")),
        )


# Global settings instance
settings = Settings.from_env()