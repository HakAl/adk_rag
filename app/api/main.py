"""
FastAPI application for RAG Agent with session-based auth and CSRF protection.
"""
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
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
from app.api.session_manager import (
    create_session,
    get_session,
    clear_session,
    require_session,
    require_csrf
)
import json
import asyncio

rag_app: Optional[RAGAgentApp] = None
rate_limit_store = defaultdict(list)
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = 60


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_app
    logger.info("Starting FastAPI application")
    await init_db()
    rag_app = RAGAgentApp()
    yield
    logger.info("Shutting down FastAPI application")
    await close_db()
    rag_app = None


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan
)


@app.middleware("http")
async def disable_compression_for_streams(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith("/stream"):
        if "content-encoding" in response.headers:
            del response.headers["content-encoding"]
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
    expose_headers=["X-CSRF-Token"],
)


def get_app() -> RAGAgentApp:
    if rag_app is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return rag_app


def check_rate_limit(client_id: str) -> bool:
    now = datetime.now()
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    rate_limit_store[client_id] = [
        timestamp for timestamp in rate_limit_store[client_id]
        if timestamp > cutoff
    ]
    if len(rate_limit_store[client_id]) >= RATE_LIMIT_REQUESTS:
        return False
    rate_limit_store[client_id].append(now)
    return True


async def rate_limit_dependency(request: Request):
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Input validation failed", "errors": exc.errors()}
    )


@app.exception_handler(InputSanitizationError)
async def sanitization_exception_handler(request: Request, exc: InputSanitizationError):
    logger.warning(f"Sanitization error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Input validation failed", "error": str(exc)}
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version=settings.version)


@app.post(
    "/sessions/coordinator",
    response_model=SessionCreateResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def create_coordinator_session(
    request_data: SessionCreateRequest,
    request: Request,
    response: Response,
    app: RAGAgentApp = Depends(get_app)
):
    try:
        chat_session_id = await app.create_coordinator_session(request_data.user_id)
        session_id = create_session(response, request_data.user_id, chat_session_id)
        return SessionCreateResponse(
            session_id=chat_session_id,
            user_id=request_data.user_id
        )
    except Exception as e:
        logger.error(f"Error creating coordinator session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/chat/coordinator",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def chat_coordinator(
    request_data: ChatRequest,
    request: Request,
    app: RAGAgentApp = Depends(get_app)
):
    try:
        # Try cookie-based auth first
        session = get_session(request)

        if session:
            # Cookie-based: require CSRF
            if not request.method == "GET" and request.headers.get("X-CSRF-Token") is None:
                raise HTTPException(status_code=403, detail="CSRF token required")

            from app.api.session_manager import verify_csrf_token
            if not verify_csrf_token(request):
                raise HTTPException(status_code=403, detail="Invalid CSRF token")

            user_id = session["user_id"]
            chat_session_id = session["chat_session_id"]
        else:
            # Legacy: use request body (for CLI)
            if not request_data.user_id or not request_data.session_id:
                raise HTTPException(status_code=401, detail="Authentication required")
            user_id = request_data.user_id
            chat_session_id = request_data.session_id

        response = await app.coordinator_chat(
            message=request_data.message,
            user_id=user_id,
            session_id=chat_session_id
        )

        return ChatResponse(
            response=response,
            session_id=chat_session_id,
            routing_info=None
        )

    except InputSanitizationError as e:
        logger.warning(f"Input sanitization failed: {e}")
        raise HTTPException(status_code=400, detail=f"Input validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error in chat/coordinator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/chat/coordinator/stream",
    dependencies=[Depends(rate_limit_dependency)]
)
async def chat_coordinator_stream(
    request_data: ChatRequest,
    request: Request,
    app: RAGAgentApp = Depends(get_app)
):
    async def event_generator():
        try:
            session = get_session(request)

            if session:
                from app.api.session_manager import verify_csrf_token
                if not verify_csrf_token(request):
                    error_event = {"type": "error", "data": {"message": "Invalid CSRF token"}}
                    yield f"data: {json.dumps(error_event)}\n\n"
                    return

                user_id = session["user_id"]
                chat_session_id = session["chat_session_id"]
            else:
                if not request_data.user_id or not request_data.session_id:
                    error_event = {"type": "error", "data": {"message": "Authentication required"}}
                    yield f"data: {json.dumps(error_event)}\n\n"
                    return
                user_id = request_data.user_id
                chat_session_id = request_data.session_id

            async for event in app.coordinator_chat_stream(
                message=request_data.message,
                user_id=user_id,
                session_id=chat_session_id
            ):
                sse_data = f"data: {json.dumps(event)}\n\n"
                yield sse_data
                await asyncio.sleep(0.001)

        except InputSanitizationError as e:
            logger.warning(f"Input sanitization failed: {e}")
            error_event = {"type": "error", "data": {"message": f"Input validation failed: {str(e)}"}}
            yield f"data: {json.dumps(error_event)}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}", exc_info=True)
            error_event = {"type": "error", "data": {"message": str(e)}}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@app.post("/logout")
async def logout(request: Request, response: Response):
    session = get_session(request)
    if session:
        clear_session(response, request)
        return {"message": "Logged out successfully"}
    return {"message": "No active session"}