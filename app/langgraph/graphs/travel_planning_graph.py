from __future__ import annotations

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from app.core.logger import log_info, log_error
from app.domain.travel_planning_domain import (
    PlanningStage, 
    TravelPlanningRequest, 
    TravelPlanningResponse,
    PlaceOption,
    TripOverview,
    FlightOption,
    HotelOption,
    DetailedItineraryDay
)
from app.langgraph.agents.place_suggestion_agent import PlaceSuggestionAgent
from app.langgraph.agents.trip_planning_agent import TripPlanningAgent
from app.langgraph.agents.flight_agent import FlightAgent
from app.langgraph.agents.hotel_agent import HotelAgent
from app.langgraph.agents.itinerary_agent import ItineraryAgent


class TravelPlanningState(TypedDict):
    """State for the travel planning graph."""
    messages: Annotated[List[Dict[str, Any]], add_messages]
    summary: str
    stage: PlanningStage
    selected_place: Optional[str]
    selected_dates: Optional[str]
    selected_flight: Optional[str]
    selected_hotel: Optional[str]
    origin_city: Optional[str]
    budget_range: Optional[str]
    
    # Stage outputs
    place_suggestions: Optional[List[PlaceOption]]
    trip_overview: Optional[TripOverview]
    flight_options: Optional[List[FlightOption]]
    hotel_options: Optional[List[HotelOption]]
    detailed_itinerary: Optional[List[DetailedItineraryDay]]
    
    # Response data
    suggestions: List[str]
    next_stage: Optional[PlanningStage]


class TravelPlanningGraph:
    """LangGraph-based travel planning workflow."""
    
    def __init__(self):
        self.place_agent = PlaceSuggestionAgent()
        self.trip_agent = TripPlanningAgent()
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.itinerary_agent = ItineraryAgent()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        workflow = StateGraph(TravelPlanningState)
        
        # Add nodes
        workflow.add_node("suggest_places", self._suggest_places_node)
        workflow.add_node("create_trip_overview", self._create_trip_overview_node)
        workflow.add_node("find_flights", self._find_flights_node)
        workflow.add_node("find_hotels", self._find_hotels_node)
        workflow.add_node("create_detailed_itinerary", self._create_detailed_itinerary_node)
        
        # Add conditional edges based on stage
        workflow.add_conditional_edges(
            "suggest_places",
            self._route_after_places,
            {
                "trip_overview": "create_trip_overview",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "create_trip_overview",
            self._route_after_trip_overview,
            {
                "flights": "find_flights",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "find_flights",
            self._route_after_flights,
            {
                "hotels": "find_hotels",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "find_hotels",
            self._route_after_hotels,
            {
                "detailed_itinerary": "create_detailed_itinerary",
                "end": END
            }
        )
        
        workflow.add_edge("create_detailed_itinerary", END)
        
        # Set entry point based on stage
        workflow.set_conditional_entry_point(
            self._determine_entry_point,
            {
                "suggest_places": "suggest_places",
                "create_trip_overview": "create_trip_overview",
                "find_flights": "find_flights",
                "find_hotels": "find_hotels",
                "create_detailed_itinerary": "create_detailed_itinerary"
            }
        )
        
        return workflow.compile()
    
    def _determine_entry_point(self, state: TravelPlanningState) -> str:
        """Determine which node to start with based on current stage."""
        stage = state.get("stage", PlanningStage.PLACE_SUGGESTIONS)
        
        if stage == PlanningStage.PLACE_SUGGESTIONS:
            return "suggest_places"
        elif stage == PlanningStage.TRIP_OVERVIEW:
            return "create_trip_overview"
        elif stage == PlanningStage.FLIGHTS:
            return "find_flights"
        elif stage == PlanningStage.HOTELS:
            return "find_hotels"
        elif stage == PlanningStage.DETAILED_ITINERARY:
            return "create_detailed_itinerary"
        else:
            return "suggest_places"
    
    def _suggest_places_node(self, state: TravelPlanningState) -> Dict[str, Any]:
        """Node for suggesting travel destinations."""
        log_info("Executing place suggestion node")
        
        try:
            place_suggestions = self.place_agent.suggest_places(
                messages=state["messages"],
                summary=state.get("summary", "")
            )
            
            return {
                "place_suggestions": place_suggestions,
                "suggestions": [
                    "Here are some destinations that match your preferences. Click on one to continue planning!"
                ],
                "next_stage": PlanningStage.TRIP_OVERVIEW
            }
        except Exception as e:
            log_error("Place suggestion node failed", error=str(e))
            return {
                "suggestions": ["Sorry, I couldn't generate place suggestions. Please try again."],
                "next_stage": None
            }
    
    def _create_trip_overview_node(self, state: TravelPlanningState) -> Dict[str, Any]:
        """Node for creating trip overview."""
        log_info("Executing trip overview node", destination=state.get("selected_place"))
        
        if not state.get("selected_place"):
            return {
                "suggestions": ["Please select a destination first."],
                "next_stage": PlanningStage.PLACE_SUGGESTIONS
            }
        
        try:
            trip_overview = self.trip_agent.create_trip_overview(
                destination=state["selected_place"],
                messages=state["messages"],
                summary=state.get("summary", "")
            )
            
            return {
                "trip_overview": trip_overview,
                "suggestions": [
                    f"Great! I've created a {trip_overview.num_days}-day plan for {trip_overview.destination}.",
                    "Ready to look at flight options?"
                ],
                "next_stage": PlanningStage.FLIGHTS
            }
        except Exception as e:
            log_error("Trip overview node failed", error=str(e))
            return {
                "suggestions": ["Sorry, I couldn't create the trip overview. Please try again."],
                "next_stage": None
            }
    
    def _find_flights_node(self, state: TravelPlanningState) -> Dict[str, Any]:
        """Node for finding flight options."""
        log_info("Executing flight search node")
        
        if not state.get("selected_place") or not state.get("origin_city"):
            return {
                "suggestions": ["I need to know your origin city to find flights."],
                "next_stage": None
            }
        
        try:
            flight_options = self.flight_agent.find_flights(
                origin_city=state["origin_city"],
                destination=state["selected_place"],
                dates=state.get("selected_dates", ""),
                budget_range=state.get("budget_range", "mid-range")
            )
            
            return {
                "flight_options": flight_options,
                "suggestions": [
                    f"Found {len(flight_options)} flight options for you.",
                    "Select your preferred flight to continue with hotel options."
                ],
                "next_stage": PlanningStage.HOTELS
            }
        except Exception as e:
            log_error("Flight search node failed", error=str(e))
            return {
                "suggestions": ["Sorry, I couldn't find flight options. Please try again."],
                "next_stage": None
            }
    
    def _find_hotels_node(self, state: TravelPlanningState) -> Dict[str, Any]:
        """Node for finding hotel options."""
        log_info("Executing hotel search node")
        
        if not state.get("selected_place"):
            return {
                "suggestions": ["Please select a destination first."],
                "next_stage": PlanningStage.PLACE_SUGGESTIONS
            }
        
        try:
            hotel_options = self.hotel_agent.find_hotels(
                destination=state["selected_place"],
                dates=state.get("selected_dates", ""),
                budget_range=state.get("budget_range", "mid-range")
            )
            
            return {
                "hotel_options": hotel_options,
                "suggestions": [
                    f"Found {len(hotel_options)} hotel options in {state['selected_place']}.",
                    "Select your preferred hotel to get your detailed itinerary."
                ],
                "next_stage": PlanningStage.DETAILED_ITINERARY
            }
        except Exception as e:
            log_error("Hotel search node failed", error=str(e))
            return {
                "suggestions": ["Sorry, I couldn't find hotel options. Please try again."],
                "next_stage": None
            }
    
    def _create_detailed_itinerary_node(self, state: TravelPlanningState) -> Dict[str, Any]:
        """Node for creating detailed itinerary."""
        log_info("Executing detailed itinerary node")
        
        trip_overview = state.get("trip_overview")
        selected_hotel = state.get("selected_hotel", "Selected Hotel")
        
        if not trip_overview:
            return {
                "suggestions": ["I need the trip overview to create a detailed itinerary."],
                "next_stage": PlanningStage.TRIP_OVERVIEW
            }
        
        try:
            detailed_itinerary = self.itinerary_agent.create_detailed_itinerary(
                trip_overview=trip_overview,
                selected_hotel=selected_hotel,
                messages=state["messages"]
            )
            
            return {
                "detailed_itinerary": detailed_itinerary,
                "suggestions": [
                    f"Your complete {trip_overview.num_days}-day itinerary is ready!",
                    "All distances and timings have been verified. Have a great trip!"
                ],
                "next_stage": None
            }
        except Exception as e:
            log_error("Detailed itinerary node failed", error=str(e))
            return {
                "suggestions": ["Sorry, I couldn't create the detailed itinerary. Please try again."],
                "next_stage": None
            }
    
    def _route_after_places(self, state: TravelPlanningState) -> str:
        """Route after place suggestions."""
        if state.get("selected_place"):
            return "trip_overview"
        return "end"
    
    def _route_after_trip_overview(self, state: TravelPlanningState) -> str:
        """Route after trip overview creation."""
        if state.get("origin_city"):
            return "flights"
        return "end"
    
    def _route_after_flights(self, state: TravelPlanningState) -> str:
        """Route after flight search."""
        if state.get("selected_flight"):
            return "hotels"
        return "end"
    
    def _route_after_hotels(self, state: TravelPlanningState) -> str:
        """Route after hotel search."""
        if state.get("selected_hotel"):
            return "detailed_itinerary"
        return "end"
    
    def plan_travel(self, request: TravelPlanningRequest) -> TravelPlanningResponse:
        """Execute the travel planning workflow."""
        
        # Initialize state
        initial_state = TravelPlanningState(
            messages=request.messages,
            summary=request.previous_summary or "",
            stage=request.stage,
            selected_place=request.selected_place,
            selected_dates=request.selected_dates,
            selected_flight=request.selected_flight,
            selected_hotel=request.selected_hotel,
            origin_city=request.origin_city,
            budget_range=request.budget_range,
            place_suggestions=None,
            trip_overview=None,
            flight_options=None,
            hotel_options=None,
            detailed_itinerary=None,
            suggestions=[],
            next_stage=None
        )
        
        try:
            # Execute the graph
            result = self.graph.invoke(initial_state)
            
            # Build response
            response = TravelPlanningResponse(
                stage=request.stage,
                summary=result.get("summary", ""),
                place_suggestions=result.get("place_suggestions"),
                trip_overview=result.get("trip_overview"),
                flight_options=result.get("flight_options"),
                hotel_options=result.get("hotel_options"),
                detailed_itinerary=result.get("detailed_itinerary"),
                next_stage=result.get("next_stage"),
                suggestions=result.get("suggestions", [])
            )
            
            log_info("Travel planning completed", stage=request.stage, next_stage=response.next_stage)
            return response
            
        except Exception as e:
            log_error("Travel planning graph execution failed", error=str(e))
            return TravelPlanningResponse(
                stage=request.stage,
                summary="",
                suggestions=["Sorry, something went wrong. Please try again."]
            )
