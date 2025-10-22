"""
Direct chat routes - bypasses coordinator for direct provider communication.
"""
import json
import asyncio
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from anthropic import AsyncAnthropic, APIError
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from config import settings, logger
from app.api.models import ChatRequest
from app.api.auth_middleware import get_current_user
from app.api.session_manager import get_session, verify_csrf_token
from app.api.rate_limiter import check_rate_limit, RATE_LIMITS
from app.db.models import User
from app.services.cloud_router_anthropic import CloudRouterAnthropicService
from app.services.cloud_router_google import CloudRouterGoogleService


router = APIRouter(prefix="/chat/direct", tags=["direct-chat"])


def get_client_id(request: Request) -> str:
    """Get client identifier (IP address)."""
    return request.client.host if request.client else "unknown"


async def chat_rate_limit(request: Request, current_user: User = Depends(get_current_user)):
    """Rate limit for authenticated chat endpoints."""
    # Check if CLI (has Authorization header with Bearer token)
    if request.headers.get("Authorization", "").startswith("Bearer "):
        # CLI request - no rate limit
        return

    # Use user_id for authenticated rate limiting
    client_id = str(current_user.id)

    if not await check_rate_limit(client_id, "auth_chat", RATE_LIMITS["auth_chat"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Chat rate limit exceeded. Please slow down."
        )


@router.post(
    "/anthropic/stream",
    dependencies=[Depends(chat_rate_limit)]
)
async def chat_direct_anthropic_stream(
        request_data: ChatRequest,
        request: Request,
        current_user: User = Depends(get_current_user)
):
    """
    Stream chat directly to Anthropic API (bypasses coordinator).
    Requires user's own API key in X-API-Key header or uses .env key for dev.
    """
    async def event_generator():
        try:
            # Verify session and CSRF
            session = await get_session(request)
            if not session:
                error_event = {"type": "error", "data": {"message": "Session required"}}
                yield f"data: {json.dumps(error_event)}\n\n"
                return

            if not await verify_csrf_token(request):
                error_event = {"type": "error", "data": {"message": "Invalid CSRF token"}}
                yield f"data: {json.dumps(error_event)}\n\n"
                return

            # Get API key from header or fall back to .env
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                # Dev fallback to .env
                api_key = settings.anthropic_api_key
                if not api_key:
                    error_event = {"type": "error", "data": {"message": "API key required"}}
                    yield f"data: {json.dumps(error_event)}\n\n"
                    return

            # Create client with user's API key (never stored)
            client = AsyncAnthropic(api_key=api_key)

            # Stream response directly from Anthropic
            async with client.messages.stream(
                model=settings.anthropic_model,
                max_tokens=2048,
                temperature=0.7,
                messages=[{"role": "user", "content": request_data.message}]
            ) as stream:
                async for text in stream.text_stream:
                    content_event = {"type": "content", "data": {"content": text}}
                    yield f"data: {json.dumps(content_event)}\n\n"
                    await asyncio.sleep(0.001)

            # Send done event
            done_event = {"type": "done", "data": {}}
            yield f"data: {json.dumps(done_event)}\n\n"

        except APIError as e:
            logger.error(f"Anthropic API error: {e}", exc_info=True)
            error_event = {"type": "error", "data": {"message": f"Anthropic API error: {str(e)}"}}
            yield f"data: {json.dumps(error_event)}\n\n"
        except Exception as e:
            logger.error(f"Error in direct Anthropic streaming: {e}", exc_info=True)
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


@router.post(
    "/anthropic/classify",
    dependencies=[Depends(chat_rate_limit)]
)
async def classify_anthropic(
        request_data: ChatRequest,
        request: Request,
        current_user: User = Depends(get_current_user)
):
    """
    Classify message using Anthropic router (non-streaming).
    Returns routing decision for client-side coordination.
    """
    try:
        # Verify session and CSRF
        session = await get_session(request)
        if not session:
            raise HTTPException(status_code=401, detail="Session required")

        if not await verify_csrf_token(request):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")

        # Get API key from header or fall back to .env
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            api_key = settings.anthropic_api_key
            if not api_key:
                raise HTTPException(status_code=400, detail="API key required")

        # Create router with user's API key
        # Note: CloudRouterAnthropicService needs to be modified to accept api_key
        # For now, it uses settings.anthropic_api_key
        router_service = CloudRouterAnthropicService()
        routing_decision = router_service.route(request_data.message)

        # Filter out rag_query (not supported in direct mode)
        routing_decision = _filter_rag_from_routing(routing_decision)

        return routing_decision

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Anthropic classification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/google/classify",
    dependencies=[Depends(chat_rate_limit)]
)
async def classify_google(
        request_data: ChatRequest,
        request: Request,
        current_user: User = Depends(get_current_user)
):
    """
    Classify message using Google router (non-streaming).
    Returns routing decision for client-side coordination.
    """
    try:
        # Verify session and CSRF
        session = await get_session(request)
        if not session:
            raise HTTPException(status_code=401, detail="Session required")

        if not await verify_csrf_token(request):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")

        # Get API key from header or fall back to .env
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            api_key = settings.google_api_key
            if not api_key:
                raise HTTPException(status_code=400, detail="API key required")

        # Create router with user's API key
        # Note: CloudRouterGoogleService needs to be modified to accept api_key
        # For now, it uses settings.google_api_key
        router_service = CloudRouterGoogleService()
        routing_decision = router_service.route(request_data.message)

        # Filter out rag_query (not supported in direct mode)
        routing_decision = _filter_rag_from_routing(routing_decision)

        return routing_decision

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Google classification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _filter_rag_from_routing(routing_decision: dict) -> dict:
    """
    Filter out rag_query from routing decisions (not supported in direct mode).

    Args:
        routing_decision: Original routing decision

    Returns:
        Filtered routing decision
    """
    # If primary agent is rag_query, change to general_chat
    if routing_decision.get("primary_agent") == "rag_query":
        logger.info("Replacing rag_query primary agent with general_chat (not supported in direct mode)")
        routing_decision["primary_agent"] = "general_chat"
        routing_decision["reasoning"] = "RAG not supported in direct mode, using general chat"

    # Remove rag_query from parallel agents
    parallel_agents = routing_decision.get("parallel_agents", [])
    if "rag_query" in parallel_agents:
        logger.info("Removing rag_query from parallel agents (not supported in direct mode)")
        routing_decision["parallel_agents"] = [
            agent for agent in parallel_agents if agent != "rag_query"
        ]

    return routing_decision


@router.post(
    "/google/stream",
    dependencies=[Depends(chat_rate_limit)]
)
async def chat_direct_google_stream(
        request_data: ChatRequest,
        request: Request,
        current_user: User = Depends(get_current_user)
):
    """
    Stream chat directly to Google Gemini API (bypasses coordinator).
    Requires user's own API key in X-API-Key header or uses .env key for dev.
    """
    async def event_generator():
        try:
            # Verify session and CSRF
            session = await get_session(request)
            if not session:
                error_event = {"type": "error", "data": {"message": "Session required"}}
                yield f"data: {json.dumps(error_event)}\n\n"
                return

            if not await verify_csrf_token(request):
                error_event = {"type": "error", "data": {"message": "Invalid CSRF token"}}
                yield f"data: {json.dumps(error_event)}\n\n"
                return

            # Get API key from header or fall back to .env
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                # Dev fallback to .env
                api_key = settings.google_api_key
                if not api_key:
                    error_event = {"type": "error", "data": {"message": "API key required"}}
                    yield f"data: {json.dumps(error_event)}\n\n"
                    return

            # Configure Google API with user's key (never stored)
            genai.configure(api_key=api_key)

            # Create model
            model = genai.GenerativeModel(
                settings.google_model,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                }
            )

            # Create streaming response in executor (Google SDK is sync)
            loop = asyncio.get_event_loop()

            def create_stream():
                return model.generate_content(request_data.message, stream=True)

            response_iterator = await loop.run_in_executor(None, create_stream)

            # Stream chunks
            for chunk in response_iterator:
                if chunk.text:
                    content_event = {"type": "content", "data": {"content": chunk.text}}
                    yield f"data: {json.dumps(content_event)}\n\n"
                    await asyncio.sleep(0.001)

            # Send done event
            done_event = {"type": "done", "data": {}}
            yield f"data: {json.dumps(done_event)}\n\n"

        except google_exceptions.ResourceExhausted as e:
            logger.error(f"Google rate limit error: {e}", exc_info=True)
            error_event = {"type": "error", "data": {"message": "Google API rate limit exceeded"}}
            yield f"data: {json.dumps(error_event)}\n\n"
        except Exception as e:
            logger.error(f"Error in direct Google streaming: {e}", exc_info=True)
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