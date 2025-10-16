"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, description="User message")
    user_id: str = Field(..., min_length=1, description="User identifier")
    session_id: str = Field(..., min_length=1, description="Session identifier")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session identifier")


class SessionCreateRequest(BaseModel):
    """Session creation request."""
    user_id: str = Field(default="api_user", description="User identifier")


class SessionCreateResponse(BaseModel):
    """Session creation response."""
    session_id: str = Field(..., description="Created session identifier")
    user_id: str = Field(..., description="User identifier")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")


class VectorStoreStats(BaseModel):
    """Vector store statistics."""
    status: str
    count: int
    collection: str
    embedding_model: Optional[str] = None


class ModelsInfo(BaseModel):
    """Models information."""
    embedding: str
    chat: str


class StatsResponse(BaseModel):
    """Statistics response."""
    app_name: str
    version: str
    environment: str
    vector_store: Dict[str, Any]
    models: Dict[str, str]