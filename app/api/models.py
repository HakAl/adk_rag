"""
API request/response models.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User's message")
    user_id: str = Field(default="local_user", description="User identifier")
    session_id: str = Field(..., description="Session identifier")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="Agent's response")
    session_id: str = Field(..., description="Session identifier")
    routing_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Routing metadata (only included when router is enabled)"
    )


class SessionCreateRequest(BaseModel):
    """Session creation request."""
    user_id: str = Field(default="local_user", description="User identifier")


class SessionCreateResponse(BaseModel):
    """Session creation response."""
    session_id: str = Field(..., description="Created session identifier")
    user_id: str = Field(..., description="User identifier")


class StatsResponse(BaseModel):
    """Application statistics response."""
    provider_type: str
    embedding_model: Optional[str] = None
    chat_model: Optional[str] = None
    vector_store_collection: str
    document_count: int
    router_enabled: bool = Field(
        default=False,
        description="Whether routing service is enabled"
    )
    router_model: Optional[str] = Field(
        default=None,
        description="Router model path if enabled"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str