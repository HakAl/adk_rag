"""
FastAPI application for RAG Agent with optional routing.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional

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


# Global app instance
rag_app: Optional[RAGAgentApp] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global rag_app
    logger.info("Starting FastAPI application")
    rag_app = RAGAgentApp()
    yield
    logger.info("Shutting down FastAPI application")
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


@app.post("/sessions", response_model=SessionCreateResponse)
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


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    app: RAGAgentApp = Depends(get_app)
):
    """
    Send a chat message and get response.

    This is the backwards-compatible endpoint that returns a simple response.
    Use /chat/extended for responses with routing metadata.
    """
    try:
        logger.info(f"Chat request received: user={request.user_id}, session={request.session_id}")

        response = await app.chat(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id
        )

        logger.info(f"Chat response type: {type(response)}")
        logger.info(f"Chat response length: {len(str(response))} chars")

        result = ChatResponse(
            response=response,
            session_id=request.session_id,
            routing_info=None  # Backwards compatible - no routing info
        )

        logger.info("Chat response created successfully")
        return result

    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/extended", response_model=ChatResponse)
async def chat_extended(
    request: ChatRequest,
    app: RAGAgentApp = Depends(get_app)
):
    """
    Send a chat message and get response with routing metadata.

    If router is enabled (ROUTER_MODEL_PATH configured), routing metadata
    will be included in the response showing which agent type handled the request.
    """
    try:
        response = await app.chat(
            message=request.message,
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
    except Exception as e:
        logger.error(f"Error in chat/extended: {e}")
        raise HTTPException(status_code=500, detail=str(e))