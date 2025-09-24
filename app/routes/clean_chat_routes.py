"""Group planning chatbot API routes (only group-plan + health)."""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import json

from app.clients.openai_client import OpenAIClient

router = APIRouter(prefix="/chat", tags=["chat"])


class GroupPlanRequest(BaseModel):
    """Batch planning request from multiple user messages with optional prior summary."""
    messages: List[Dict[str, Any]]  # expects items with keys: role (user/assistant), content, optional user/name
    previous_summary: Optional[str] = None
    days: Optional[int] = 3
    model: Optional[str] = "gpt-3.5-turbo"


class GroupPlanResponse(BaseModel):
    """Structured planning response with extracted info and itinerary."""
    summary: str
    extracted_preferences: Dict[str, Any]
    suggestions: List[str]
    itinerary: Dict[str, Any]
    model: Optional[str] = None
    tokens_used: Optional[int] = None


## NOTE: Normal chat/session endpoints removed intentionally.


@router.get("/health")
async def chat_health():
    """Health check for chat service."""
    return {
        "status": "healthy", 
        "service": "chat",
        "active_sessions": len(chat_sessions)
    }


@router.post("/group-plan", response_model=GroupPlanResponse)
async def group_plan(request: GroupPlanRequest):
    """Ingest multiple chat messages and an optional prior summary, extract travel-relevant info, and propose suggestions + itinerary."""
    if not request.messages or not isinstance(request.messages, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="messages must be a non-empty list"
        )

    try:
        openai_client = OpenAIClient()

        system_prompt = (
            "You are a helpful AI travel planner assisting a group of people in planning a trip together.\n"
            "You are given:\n"
            "1. The ongoing chat messages (recent ones).\n"
            "2. A running summary of the conversation so far.\n\n"
            "Your role:\n"
            "- Understand what the group has already discussed and agreed on.\n"
            "- Identify what details are still missing or undecided (e.g., destinations, dates, activities, budget, food preferences).\n"
            "- Ask clear and concise clarifying questions when necessary.\n"
            "- Suggest relevant destinations, activities, restaurants, or itineraries based on what's known.\n"
            "- Do NOT generate an itinerary by default. If (and only if) all key trip details appear sufficient for an itinerary, include a short suggestion asking if the group would like you to generate an itinerary next. Otherwise, ask concise clarifying questions to fill missing details.\n"
            "- Keep your tone friendly, neutral, and inclusive, ensuring no single person is favored.\n"
            "- Do not dominate the conversation—only assist when explicitly invoked.\n\n"
            "IMPORTANT OUTPUT FORMAT (STRICT JSON):\n"
            "Return a compact JSON object with these keys only: \n"
            "- summary: short updated summary of known decisions and context.\n"
            "- extracted_preferences: an object with fields like dates/timeframe, origin, headcount, budget, food/diet, mobility_constraints, activity_preferences, destinations, lodging_preferences, transportation, constraints, additional_preferences.\n"
            "- suggestions: an array of short strings including clarifying questions and/or a single question like 'Would you like me to generate an itinerary now?' when details are sufficient.\n"
            "- itinerary: ALWAYS return an empty object {} at this step. Do not include day-by-day content unless explicitly requested later.\n"
        )

        # Compose input for the model
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

        if request.previous_summary:
            messages.append({
                "role": "system",
                "content": f"Previous summary (use as prior context, update if needed):\n{request.previous_summary}"
            })

        # Add the provided messages as user context in a compact JSON bundle to avoid token bloat
        compact_payload = json.dumps({
            "messages": request.messages,
            "days": request.days
        })
        messages.append({
            "role": "user",
            "content": f"Here is the batch of messages and requested days as JSON:\n{compact_payload}"
        })

        ai = openai_client.chat(messages, model=request.model)

        # Try to parse JSON; if the model returns text, try to find JSON substring
        raw = ai["content"].strip()
        parsed: Dict[str, Any]
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Heuristic: find first { and last }
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                parsed = json.loads(raw[start:end+1])
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI response could not be parsed as JSON"
                )

        # Normalize types to satisfy response model
        summary = parsed.get("summary", "")
        extracted_preferences = parsed.get("extracted_preferences", {})
        suggestions = parsed.get("suggestions", [])
        itinerary = {}

        # Coerce extracted_preferences to dict
        if not isinstance(extracted_preferences, dict):
            try:
                extracted_preferences = dict(extracted_preferences)  # may raise
            except Exception:
                extracted_preferences = {"value": extracted_preferences}

        # Coerce suggestions to list[str]
        if not isinstance(suggestions, list):
            if isinstance(suggestions, dict):
                suggestions = [f"{k}: {v}" for k, v in suggestions.items()]
            elif suggestions is None:
                suggestions = []
            else:
                suggestions = [str(suggestions)]

        # Coerce itinerary to dict[str, Any]
        # Force itinerary empty at this step per product requirement

        return GroupPlanResponse(
            summary=summary,
            extracted_preferences=extracted_preferences,
            suggestions=suggestions,
            itinerary=itinerary,
            model=ai.get("model"),
            tokens_used=(ai.get("usage") or {}).get("total_tokens")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate group plan: {str(e)}"
        )
