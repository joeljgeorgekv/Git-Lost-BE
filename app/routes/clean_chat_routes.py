"""Group planning chatbot API routes (only group-plan + health)."""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, status

from app.domain.chat_domain import GroupPlanRequest, GroupPlanResponse
from app.services.chat_plan_service import ChatPlanService

router = APIRouter(prefix="/chat", tags=["chat"])
service = ChatPlanService()

## NOTE: Normal chat/session endpoints removed intentionally.


@router.get("/health")
async def chat_health():
    """Health check for chat service."""
    return {
        "status": "healthy",
        "service": "chat",
        "active_sessions": 0
    }


@router.post("/group-plan", response_model=GroupPlanResponse)
async def group_plan(request: GroupPlanRequest):
    """Ingest multiple chat messages and an optional prior summary and return extracted info.

    All AI logic is handled by ChatPlanService for testability and reuse.
    """
    try:
        return service.group_plan(request)
    except ValueError as e:
        msg = str(e)
        if msg == "messages_invalid":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="messages must be a non-empty list")
        if msg == "ai_failed":
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI request failed")
        if msg == "ai_parse_failed":
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI response could not be parsed as JSON")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate group plan")
