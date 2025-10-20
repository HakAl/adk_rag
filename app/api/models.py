"""
API request/response models with input validation.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Chat request model - backwards compatible."""
    message: str = Field(
        ...,
        description="User's message",
        min_length=1,
        max_length=16000
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User identifier",
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\.]+$'
    )
    session_id: Optional[str] = Field(
        default=None,
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
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize user ID."""
        if v is None:
            return None
        from app.utils.input_sanitizer import get_sanitizer, InputSanitizationError

        try:
            return get_sanitizer().sanitize_user_id(v)
        except InputSanitizationError as e:
            raise ValueError(str(e))

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize session ID."""
        if v is None:
            return None
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


class RegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=30)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.lower().strip()
        if not v.isalnum():
            raise ValueError("Username must contain only letters and numbers")
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.lower().strip()
        if '@' not in v:
            raise ValueError("Invalid email format")
        return v


class RegisterResponse(BaseModel):
    """User registration response."""
    user_id: str
    username: str
    email: str
    message: str = "Registration successful"


class LoginRequest(BaseModel):
    """User login request."""
    username_or_email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=100)

    @field_validator('username_or_email')
    @classmethod
    def validate_username_or_email(cls, v: str) -> str:
        return v.lower().strip()


class LoginResponse(BaseModel):
    """User login response."""
    user_id: str
    username: str
    email: str
    message: str = "Login successful"


class UserResponse(BaseModel):
    """Current user response."""
    user_id: str
    username: str
    email: str
    is_active: bool
    created_at: str


class ResendVerificationRequest(BaseModel):
    """Request to resend verification email."""
    email: str = Field(..., min_length=3, max_length=255)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.lower().strip()
        if '@' not in v:
            raise ValueError("Invalid email format")
        return v


class VerifyEmailResponse(BaseModel):
    """Email verification response."""
    message: str
    verified: bool