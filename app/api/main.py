"""
FastAPI application for RAG Agent with input sanitization and rate limiting.
"""
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Optional
from pydantic import ValidationError
from collections import defaultdict
from datetime import datetime, timedelta

from config import settings, logger
from app.core.application import RAGAgentApp
from app.api.models import (
    ChatRequest,
    ChatResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    StatsResponse,
    HealthResponse
)
from app.utils.input_sanitizer import InputSanitizationError
from app.db.database import init_db, close_db
from app.db.session_service import PostgreSQLSessionService


# Global app instance
rag_app: Optional[RAGAgentApp] = None

# Simple in-memory rate limiter
# In production, use Redis or similar
rate_limit_store = defaultdict(list)
RATE_LIMIT_REQUESTS = 60  # requests per window
RATE_LIMIT_WINDOW = 60  # seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global rag_app
    logger.info("Starting FastAPI application")

    # Initialize database
    await init_db()

    rag_app = RAGAgentApp()
    yield

    logger.info("Shutting down FastAPI application")

    # Close database connections
    await close_db()

    rag_app = None


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_app() -> RAGAgentApp:
    """Dependency to get RAG app instance."""
    if rag_app is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return rag_app


def check_rate_limit(client_id: str) -> bool:
    """
    Check if client has exceeded rate limit.

    Args:
        client_id: Client identifier (user_id or IP)

    Returns:
        True if within limits, False if exceeded
    """
    now = datetime.now()
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)

    # Clean old entries
    rate_limit_store[client_id] = [
        timestamp for timestamp in rate_limit_store[client_id]
        if timestamp > cutoff
    ]

    # Check limit
    if len(rate_limit_store[client_id]) >= RATE_LIMIT_REQUESTS:
        return False

    # Add new request
    rate_limit_store[client_id].append(now)
    return True


async def rate_limit_dependency(request: Request):
    """Rate limiting dependency."""
    # Use user_id from request if available, otherwise use IP
    client_id = request.client.host if request.client else "unknown"

    if not check_rate_limit(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Input validation failed",
            "errors": exc.errors()
        }
    )


@app.exception_handler(InputSanitizationError)
async def sanitization_exception_handler(request: Request, exc: InputSanitizationError):
    """Handle input sanitization errors."""
    logger.warning(f"Sanitization error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Input validation failed",
            "error": str(exc)
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.version
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats(app: RAGAgentApp = Depends(get_app)):
    """Get application statistics."""
    try:
        stats = app.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Check if a session exists.

    Returns 200 if session exists, 404 if not found.
    """
    session_service = PostgreSQLSessionService()
    exists = await session_service.session_exists(session_id)

    if not exists:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"session_id": session_id, "status": "active"}


@app.post(
    "/sessions",
    response_model=SessionCreateResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def create_session(
    request: SessionCreateRequest,
    app: RAGAgentApp = Depends(get_app)
):
    """Create a new chat session."""
    try:
        session_id = await app.create_session(request.user_id)
        return SessionCreateResponse(
            session_id=session_id,
            user_id=request.user_id
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/sessions/coordinator",
    response_model=SessionCreateResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def create_coordinator_session(
    request: SessionCreateRequest,
    app: RAGAgentApp = Depends(get_app)
):
    """Create a new chat session for coordinator agent."""
    try:
        session_id = await app.create_coordinator_session(request.user_id)
        return SessionCreateResponse(
            session_id=session_id,
            user_id=request.user_id
        )
    except Exception as e:
        logger.error(f"Error creating coordinator session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def chat(
    request: ChatRequest,
    app: RAGAgentApp = Depends(get_app)
):
    """
    Send a chat message and get response.

    This is the backwards-compatible endpoint that returns a simple response.
    Use /chat/extended for responses with routing metadata.

    Input is automatically validated and sanitized by Pydantic validators.
    """
    try:
        logger.info(
            f"Chat request received: user={request.user_id}, "
            f"session={request.session_id[:8]}..., "
            f"message_length={len(request.message)}"
        )

        response = await app.chat(
            message=request.message,  # Already sanitized by Pydantic validators
            user_id=request.user_id,
            session_id=request.session_id
        )

        logger.info(f"Chat response generated: {len(str(response))} chars")

        result = ChatResponse(
            response=response,
            session_id=request.session_id,
            routing_info=None  # Backwards compatible - no routing info
        )

        return result

    except InputSanitizationError as e:
        logger.warning(f"Input sanitization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/chat/extended",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def chat_extended(
    request: ChatRequest,
    app: RAGAgentApp = Depends(get_app)
):
    """
    Send a chat message and get response with routing metadata.

    If router is enabled (ROUTER_MODEL_PATH configured), routing metadata
    will be included in the response showing which agent type handled the request.

    Input is automatically validated and sanitized by Pydantic validators.
    """
    try:
        logger.info(
            f"Extended chat request: user={request.user_id}, "
            f"session={request.session_id[:8]}..., "
            f"message_length={len(request.message)}"
        )

        response = await app.chat(
            message=request.message,  # Already sanitized by Pydantic validators
            user_id=request.user_id,
            session_id=request.session_id
        )

        # Get routing info if available
        routing_info = None
        last_routing = app.get_last_routing()
        if last_routing:
            routing_info = {
                "agent": last_routing["primary_agent"],
                "confidence": last_routing["confidence"],
                "reasoning": last_routing["reasoning"]
            }

        return ChatResponse(
            response=response,
            session_id=request.session_id,
            routing_info=routing_info
        )
    except InputSanitizationError as e:
        logger.warning(f"Input sanitization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in chat/extended: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/chat/coordinator",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def chat_coordinator(
    request: ChatRequest,
    app: RAGAgentApp = Depends(get_app)
):
    """
    Send a chat message and get response via coordinator with specialist delegation.

    This endpoint uses the coordinator agent which automatically routes requests
    to specialized agents based on the request type. Falls back to general chat
    if coordinator is not available.

    Input is automatically validated and sanitized by Pydantic validators.
    """
    try:
        logger.info(
            f"Coordinator chat request: user={request.user_id}, "
            f"session={request.session_id[:8]}..., "
            f"message_length={len(request.message)}"
        )

        response = await app.coordinator_chat(
            message=request.message,  # Already sanitized by Pydantic validators
            user_id=request.user_id,
            session_id=request.session_id
        )

        logger.info(f"Coordinator chat response generated: {len(str(response))} chars")

        result = ChatResponse(
            response=response,
            session_id=request.session_id,
            routing_info=None  # Can be enhanced later to show which specialist handled it
        )

        return result

    except InputSanitizationError as e:
        logger.warning(f"Input sanitization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in chat/coordinator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))