from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.domain.travel_planning_domain import TravelPlanningRequest, TravelPlanningResponse
from app.services.travel_planning_service import TravelPlanningService
from app.core.logger import log_info, log_error

router = APIRouter(prefix="/travel", tags=["travel-planning"])
service = TravelPlanningService()


@router.post("/plan", response_model=TravelPlanningResponse)
async def plan_travel(request: TravelPlanningRequest):
    """Execute the LangGraph-based travel planning workflow."""
    
    log_info(
        "Travel planning request received",
        stage=request.stage,
        selected_place=request.selected_place
    )
    
    try:
        response = service.plan_travel(request)
        return response
        
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "messages_invalid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Messages must be a non-empty list"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process travel planning request"
        )
    except Exception as e:
        log_error("Travel planning route failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during travel planning"
        )


@router.get("/health")
async def travel_health():
    """Health check for travel planning service."""
    return {
        "status": "healthy",
        "service": "travel-planning",
        "features": [
            "place_suggestions",
            "trip_overview", 
            "flight_search",
            "hotel_search",
            "detailed_itinerary"
        ]
    }
