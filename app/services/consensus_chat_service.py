from __future__ import annotations

from typing import Any, Dict, List

from app.core.logger import log_info
from app.langgraph.graphs.consensus_chat_graph import ConsensusChatGraph, ConsensusChatState
from app.schemas.consensus_chat_schema import (
    ConsensusChatResponse, 
    FlightOption, 
    HotelOption, 
    CabOption, 
    TripOverview
)


class ConsensusChatService:
    """Service orchestrating the consensus chat graph."""

    def __init__(self) -> None:
        self.graph = ConsensusChatGraph()

    def step(self, state: ConsensusChatState) -> ConsensusChatResponse:
        log_info(
            "ConsensusChatService.step",
            destination=state.get("destination"),
            user_message=state.get("user_message"),
        )
        result = self.graph.step(state)
        # sanitize non-serializable keys if any
        result.pop("messages", None)
        
        # Convert raw result to structured response
        return self._convert_to_structured_response(result, state)
    
    def _convert_to_structured_response(self, result: Dict[str, Any], original_state: ConsensusChatState) -> ConsensusChatResponse:
        """Convert raw graph result to structured ConsensusChatResponse."""
        
        # Convert flight options
        flight_options = []
        if result.get("flight_options"):
            for flight in result["flight_options"]:
                if isinstance(flight, dict):
                    flight_options.append(FlightOption(**flight))
                else:
                    flight_options.append(FlightOption())
        
        # Convert hotel options
        hotel_options = []
        if result.get("hotel_options"):
            for hotel in result["hotel_options"]:
                if isinstance(hotel, dict):
                    hotel_options.append(HotelOption(**hotel))
                else:
                    hotel_options.append(HotelOption())
        
        # Convert cab options
        cab_transfer_options = []
        if result.get("cab_transfer_options"):
            for cab in result["cab_transfer_options"]:
                if isinstance(cab, dict):
                    cab_transfer_options.append(CabOption(**cab))
                else:
                    cab_transfer_options.append(CabOption())
        
        cab_day_options = []
        if result.get("cab_day_options"):
            for cab in result["cab_day_options"]:
                if isinstance(cab, dict):
                    cab_day_options.append(CabOption(**cab))
                else:
                    cab_day_options.append(CabOption())
        
        # Convert trip overview
        trip_overview = None
        if result.get("trip_overview"):
            overview_data = result["trip_overview"]
            if isinstance(overview_data, dict):
                trip_overview = TripOverview(**overview_data)
            else:
                trip_overview = TripOverview()
        
        # Convert selected items
        selected_flight = None
        if result.get("selected_flight") and isinstance(result["selected_flight"], dict):
            selected_flight = FlightOption(**result["selected_flight"])
        
        selected_hotel = None
        if result.get("selected_hotel") and isinstance(result["selected_hotel"], dict):
            selected_hotel = HotelOption(**result["selected_hotel"])
        
        # Extract suggestions
        suggestions = result.get("suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = []
        
        return ConsensusChatResponse(
            destination=result.get("destination"),
            dates=result.get("dates"),
            route_taken=result.get("route_taken"),
            trip_overview=trip_overview,
            flight_options=flight_options,
            hotel_options=hotel_options,
            cab_transfer_options=cab_transfer_options,
            cab_day_options=cab_day_options,
            suggestions=suggestions,
            selected_flight=selected_flight,
            selected_hotel=selected_hotel,
            user_message=original_state.get("user_message"),
            origin_city=original_state.get("origin_city"),
            budget_range=original_state.get("budget_range"),
            passengers=original_state.get("passengers"),
            needs_flight=original_state.get("needs_flight")
        )

