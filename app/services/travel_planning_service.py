from __future__ import annotations

from app.core.logger import log_info, log_error
from app.domain.travel_planning_domain import TravelPlanningRequest, TravelPlanningResponse
from app.langgraph.graphs.travel_planning_graph import TravelPlanningGraph


class TravelPlanningService:
    """Service that orchestrates the complete travel planning workflow using LangGraph."""
    
    def __init__(self):
        self.planning_graph = TravelPlanningGraph()
    
    def plan_travel(self, request: TravelPlanningRequest) -> TravelPlanningResponse:
        """Execute the travel planning workflow based on current stage."""
        
        log_info(
            "Travel planning request received",
            stage=request.stage,
            selected_place=request.selected_place,
            origin_city=request.origin_city
        )
        
        try:
            # Execute the LangGraph workflow
            response = self.planning_graph.plan_travel(request)
            
            log_info(
                "Travel planning completed",
                stage=request.stage,
                next_stage=response.next_stage,
                has_suggestions=len(response.suggestions) > 0
            )
            
            return response
            
        except Exception as e:
            log_error("Travel planning service failed", error=str(e), stage=request.stage)
            
            # Return error response
            return TravelPlanningResponse(
                stage=request.stage,
                summary="",
                suggestions=["I encountered an error while planning your trip. Please try again."]
            )
