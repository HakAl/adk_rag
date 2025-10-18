"""
API request/response models with input validation.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Chat request model with validation."""
    message: str = Field(
        ...,
        description="User's message",
        min_length=1,
        max_length=16000  # Increased to match sanitizer config
    )
    user_id: str = Field(
        default="local_user",
        description="User identifier",
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\.]+$'
    )
    session_id: str = Field(
        ...,
        description="Session identifier",
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9\-]+$'
    )

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate and sanitize message."""
        from app.utils.input_sanitizer import get_sanitizer, InputSanitizationError

        try:
            return get_sanitizer().sanitize_message(v)
        except InputSanitizationError as e:
            raise ValueError(str(e))

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate and sanitize user ID."""
        from app.utils.input_sanitizer import get_sanitizer, InputSanitizationError

        try:
            return get_sanitizer().sanitize_user_id(v)
        except InputSanitizationError as e:
            raise ValueError(str(e))

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate and sanitize session ID."""
        from app.utils.input_sanitizer import get_sanitizer, InputSanitizationError

        try:
            return get_sanitizer().sanitize_session_id(v)
        except InputSanitizationError as e:
            raise ValueError(str(e))


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="Agent's response")
    session_id: str = Field(..., description="Session identifier")
    routing_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Routing metadata (only included when router is enabled)"
    )


class SessionCreateRequest(BaseModel):
    """Session creation request with validation."""
    user_id: str = Field(
        default="local_user",
        description="User identifier",
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\.]+$'
    )

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate and sanitize user ID."""
        from app.utils.input_sanitizer import get_sanitizer, InputSanitizationError

        try:
            return get_sanitizer().sanitize_user_id(v)
        except InputSanitizationError as e:
            raise ValueError(str(e))


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