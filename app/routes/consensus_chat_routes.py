from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.logger import log_error
from app.schemas.consensus_schema import ConsensusRequest, ConsensusPayload
from app.schemas.consensus_chat_schema import ConsensusChatRequest, ConsensusChatResponse
from app.services.consensus_chat_service import ConsensusChatService

router = APIRouter(prefix="/consensus-chat", tags=["consensus-chat"])
service = ConsensusChatService()


@router.post("/step", response_model=ConsensusChatResponse)
async def consensus_chat_step(request: ConsensusChatRequest):
    """Drive one step of the consensus chat graph. Returns options/suggestions.

    The request includes a latest user message and the consensus payload. The
    graph decides whether to surface flights, hotels, cabs, or a detailed itinerary
    based on message and context. Gibberish messages do not alter state.
    """
    try:
        state = {
            "user_message": request.user_message,
            "messages": request.messages,
            "destination": request.consensus.destination,
            "dates": request.consensus.dates.display or f"{request.consensus.dates.start} - {request.consensus.dates.end}",
            "origin_city": request.origin_city,
            "budget_range": request.budget_range,
            "passengers": request.passengers,
            "needs_flight": request.needs_flight,
            "selected_flight": None,
            "selected_hotel": None,
            "flights_limit": request.flights_limit,
            "flights_offset": request.flights_offset,
            "hotels_limit": request.hotels_limit,
            "hotels_offset": request.hotels_offset,
            "cabs_limit": request.cabs_limit,
            "cabs_transfer_offset": request.cabs_transfer_offset,
            "cabs_day_offset": request.cabs_day_offset,
            # defaults that may be filled by the graph
            "trip_overview": None,
            "flight_options": None,
            "hotel_options": None,
            "cab_transfer_options": None,
            "cab_day_options": None,
            "suggestions": [],
            "route_taken": None,
        }
        return service.step(state)
    except Exception as e:
        log_error("consensus-chat step failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process consensus chat step",
        )
