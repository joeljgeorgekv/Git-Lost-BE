from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.core.logger import log_info, log_error
from app.domain.chat_domain import GroupPlanRequest, GroupPlanResponse
from app.domain.travel_planning_domain import TravelPlanningRequest, PlanningStage
from app.services.travel_planning_service import TravelPlanningService


class ChatAnalysis(BaseModel):
    """Structured output for chat context analysis."""
    stage: str
    summary: str
    extracted_preferences: Dict[str, Any]
    selected_place: Optional[str] = None
    selected_dates: Optional[str] = None
    origin_city: Optional[str] = None
    budget_range: str = "mid-range"


class ChatPlanService:
    """Service that generates a structured group planning response from chat messages."""

    def __init__(self) -> None:
        self.travel_planning_service = TravelPlanningService()
        
        # Initialize LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )

    def group_plan(self, request: GroupPlanRequest) -> GroupPlanResponse:
        """Generate group planning response using the new LangGraph-based travel planning flow."""
        if not request.messages or not isinstance(request.messages, list):
            raise ValueError("messages_invalid")

        try:
            # Analyze messages to determine what stage we're in and extract preferences
            analysis = self._analyze_chat_context(request)
            
            # Create travel planning request
            travel_request = TravelPlanningRequest(
                messages=request.messages,
                previous_summary=request.previous_summary,
                stage=analysis["stage"],
                selected_place=analysis.get("selected_place"),
                selected_dates=analysis.get("selected_dates"),
                origin_city=analysis.get("origin_city"),
                budget_range=analysis.get("budget_range", "mid-range")
            )
            
            # Execute travel planning workflow
            travel_response = self.travel_planning_service.plan_travel(travel_request)
            
            # Convert to GroupPlanResponse format
            return GroupPlanResponse(
                summary=travel_response.summary or analysis["summary"],
                extracted_preferences=analysis["extracted_preferences"],
                suggestions=travel_response.suggestions,
                itinerary={},  # Keep empty for now, detailed itinerary comes later
                model=request.model,
                tokens_used=None
            )
            
        except Exception as e:
            log_error("group plan failed", error=str(e))
            # Fallback to original simple response
            return self._fallback_group_plan(request)
    
    def _analyze_chat_context(self, request: GroupPlanRequest) -> Dict[str, Any]:
        """Analyze chat messages to determine current stage and extract preferences using structured output."""
        
        system_prompt = """
        Analyze the chat messages and determine:
        1. What stage of travel planning they're in
        2. Extract any preferences mentioned
        
        For the stage field, use one of: place_suggestions, trip_overview, flights, hotels, detailed_itinerary
        
        Extract preferences like destinations, origin city, budget level, dates, and activities mentioned.
        """
        
        try:
            # Create structured output chain
            structured_llm = self.llm.with_structured_output(ChatAnalysis)
            
            # Prepare the input message
            chat_context = json.dumps({"messages": request.messages[-10:]})
            
            # Get structured analysis
            analysis_result = structured_llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze these chat messages: {chat_context}"}
            ])
            
            # Map stage string to enum
            stage_map = {
                "place_suggestions": PlanningStage.PLACE_SUGGESTIONS,
                "trip_overview": PlanningStage.TRIP_OVERVIEW,
                "flights": PlanningStage.FLIGHTS,
                "hotels": PlanningStage.HOTELS,
                "detailed_itinerary": PlanningStage.DETAILED_ITINERARY
            }
            
            # Convert to dict and map stage
            analysis = analysis_result.dict()
            analysis["stage"] = stage_map.get(analysis.get("stage", "place_suggestions"), PlanningStage.PLACE_SUGGESTIONS)
            
            log_info("chat analysis completed", stage=analysis["stage"], has_place=bool(analysis.get("selected_place")))
            return analysis
            
        except Exception as e:
            log_error("chat analysis failed", error=str(e))
            return {
                "stage": PlanningStage.PLACE_SUGGESTIONS,
                "summary": "Group discussing travel plans",
                "extracted_preferences": {},
                "selected_place": None,
                "selected_dates": None,
                "origin_city": None,
                "budget_range": "mid-range"
            }
    
    def _fallback_group_plan(self, request: GroupPlanRequest) -> GroupPlanResponse:
        """Fallback to simple response if advanced planning fails."""
        return GroupPlanResponse(
            summary="Group discussing travel plans",
            extracted_preferences={
                "status": "analyzing preferences",
                "stage": "initial_planning"
            },
            suggestions=[
                "I'm here to help plan your trip!",
                "What destination are you considering?",
                "When are you planning to travel?"
            ],
            itinerary={},
            model=request.model,
            tokens_used=None
        )
