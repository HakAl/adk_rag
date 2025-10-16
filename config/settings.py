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
    retrieval_k: int = 5
    
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
        )


# Global settings instance
settings = Settings.from_env()
