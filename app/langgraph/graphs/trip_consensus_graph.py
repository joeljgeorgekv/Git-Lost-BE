from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.logger import log_info, log_error
from app.core.config import settings
from app.clients.google_places_client import GooglePlacesClient


class TravelSummary(BaseModel):
    """Structured travel summary extracted from messages."""
    budget_min: Optional[int] = Field(None, description="Minimum budget per person")
    budget_max: Optional[int] = Field(None, description="Maximum budget per person")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    preferred_places: List[str] = Field(default_factory=list, description="List of preferred destinations")
    travel_preferences: List[str] = Field(default_factory=list, description="Travel preferences like food, history, nature, etc.")
    must_haves: List[str] = Field(default_factory=list, description="Must-have requirements")


class PlaceCandidate(BaseModel):
    """A candidate travel destination."""
    place_name: str = Field(description="Name of the destination")
    budget: str = Field(description="Budget category: budget, mid-range, or luxury")
    best_time: List[str] = Field(description="Best months to visit")
    why_it_matches: List[str] = Field(description="Reasons why this place matches preferences")


class PlaceCandidates(BaseModel):
    """List of place candidates."""
    candidates: List[PlaceCandidate] = Field(description="List of 3-5 destination candidates")


class ConsensusCard(BaseModel):
    """Final consensus travel card."""
    date: str = Field(description="Start date in YYYY-MM-DD format")
    no_of_days: int = Field(description="Number of days for the trip")
    weekdays_range: str = Field(description="Day range like 'Thu–Mon'")
    accommodation_cost_per_person: int = Field(description="Accommodation cost per person")
    transportation_cost_per_person: int = Field(description="Transportation cost per person")
    flight_cost_per_person: int = Field(description="Flight cost per person")
    places: List[Dict[str, Any]] = Field(description="List of places with details")


class TripConsensusState(TypedDict):
    # Input
    trip_id: str
    new_messages: List[Dict[str, Any]]  # Raw message objects
    
    # Processing state
    summary: Optional[Dict[str, Any]]
    candidates: List[Dict[str, Any]]
    selected_places: List[Dict[str, Any]]  # Places that users are converging on
    consensus_card: Optional[Dict[str, Any]]
    
    # Flow control
    status: str  # "processing", "multiple_candidates", "converging", "finalized", "no_new_messages"
    next_node: Optional[str]


class TripConsensusGraph:
    """LangGraph for trip planning consensus flow with Summarizer, Place Suggestion, and Consensus nodes."""
    
    def __init__(self) -> None:
        base_llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0, 
            openai_api_key=settings.openai_api_key
        )
        
        # Create structured LLMs for each task
        self.summary_llm = base_llm.with_structured_output(TravelSummary)
        self.candidates_llm = base_llm.with_structured_output(PlaceCandidates)
        self.selection_llm = base_llm.with_structured_output(PlaceCandidates)  # For place selection/reduction
        self.consensus_llm = base_llm.with_structured_output(ConsensusCard)
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        sg = StateGraph(TripConsensusState)
        
        # Add nodes
        sg.add_node("check_messages", self._check_messages)
        sg.add_node("summarizer", self._summarizer)
        sg.add_node("place_suggestion", self._place_suggestion)
        sg.add_node("place_selection", self._place_selection)  # New node for reducing candidates
        sg.add_node("consensus", self._consensus)
        
        # Define edges - simplified flow without unnecessary exits
        sg.add_edge("check_messages", "summarizer")
        sg.add_edge("summarizer", "place_suggestion")
        sg.add_edge("place_suggestion", "place_selection")
        
        sg.add_conditional_edges(
            "place_selection",
            self._route_after_selection,
            {
                "consensus": "consensus",
                "end": END  # Only exit if we can't reach consensus
            }
        )
        
        sg.add_edge("consensus", END)
        
        # Set entry point
        sg.set_entry_point("check_messages")
        
        return sg.compile()
    
    # Routing functions for conditional edges
    
    def _route_after_selection(self, state: TripConsensusState) -> str:
        """Route after place selection - key logic for consensus."""
        selected_places = state.get("selected_places", [])
        
        if not selected_places:
            log_info("TripConsensus: no places selected, ending")
            return "end"
        elif len(selected_places) == 1:
            log_info("TripConsensus: single place selected, proceeding to consensus")
            return "consensus"
        else:
            # Multiple places - end with multiple candidates status
            log_info("TripConsensus: multiple places selected, ending with multiple candidates", 
                    place_count=len(selected_places))
            return "end"
    
    
    def _check_messages(self, state: TripConsensusState) -> Dict[str, Any]:
        """Check if there are new messages to process."""
        new_messages = state.get("new_messages", [])
        
        if not new_messages:
            log_info("TripConsensus: no new messages, proceeding with existing data")
            return {
                "status": "no_new_messages"
            }
        
        log_info("TripConsensus: processing messages", count=len(new_messages))
        return {
            "status": "processing"
        }
    
    def _summarizer(self, state: TripConsensusState) -> Dict[str, Any]:
        """Summarize new messages into structured format using LLM."""
        try:
            new_messages = state.get("new_messages", [])
            log_info("TripConsensus: summarizer starting", message_count=len(new_messages))
            
            messages_text = [msg.get("message", "") for msg in new_messages]
            text_blob = "\n".join(messages_text)
            log_info("TripConsensus: text extracted", text_length=len(text_blob))
            
            # Use structured LLM to extract summary
            system_prompt = """
            You are a travel planning assistant. Extract structured information from user messages.
            Only extract information that is explicitly mentioned in the messages.
            """
            
            user_prompt = f"Extract travel information from these messages:\n{text_blob}"
            log_info("TripConsensus: calling structured LLM for summarization")
            
            try:
                summary_obj = self.summary_llm.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ])
                
                # Convert Pydantic model to dict
                summary = summary_obj.model_dump()
                log_info("TripConsensus: structured output successful", summary=summary)
                
            except Exception as llm_err:
                log_error("TripConsensus: structured LLM failed", error=str(llm_err))
                # Fallback to heuristic extraction
                summary = self._heuristic_summary(text_blob)
                log_info("TripConsensus: using heuristic fallback", summary=summary)
            
            log_info("TripConsensus: summary generated", summary=summary)
            return {
                "summary": summary
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            log_error("TripConsensus: summarizer failed", error=str(e), traceback=error_details)
            # Fallback to heuristic
            text_blob = "\n".join([msg.get("message", "") for msg in state.get("new_messages", [])])
            return {
                "summary": self._heuristic_summary(text_blob)
            }
    
    def _heuristic_summary(self, text_blob: str) -> Dict[str, Any]:
        """Fallback heuristic extraction if LLM fails."""
        text_lower = text_blob.lower()
        
        # Extract places
        place_hints = [
            "italy", "rome", "florence", "paris", "london", "tokyo", "kyoto",
            "bali", "singapore", "new york", "barcelona", "amsterdam", "madrid",
            "berlin", "prague", "vienna", "budapest", "lisbon", "dublin"
        ]
        preferred_places = [h for h in place_hints if h in text_lower]
        
        # Extract preferences
        pref_hints = ["food", "history", "nature", "beach", "museums", "nightlife", "culture", "art"]
        travel_preferences = [h for h in pref_hints if h in text_lower]
        
        # Extract budget
        money = [int(m) for m in re.findall(r"\b\$?(\d{3,5})\b", text_blob)]
        budget_min = min(money) if money else None
        budget_max = max(money) if money else None
        
        # Extract dates
        dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", text_blob)
        start_date = dates[0] if dates else None
        end_date = dates[1] if len(dates) > 1 else None
        
        return {
            "budget_min": budget_min,
            "budget_max": budget_max,
            "start_date": start_date,
            "end_date": end_date,
            "preferred_places": preferred_places,
            "travel_preferences": travel_preferences,
            "must_haves": []
        }
    
    def _place_suggestion(self, state: TripConsensusState) -> Dict[str, Any]:
        """Suggest 3-5 candidate places based on summary using LLM."""
        try:
            summary = state.get("summary", {})
            log_info("TripConsensus: place_suggestion starting", summary=summary)
            
            system_prompt = """
            You are a travel expert. Based on user preferences, suggest 3-5 travel destinations.
            Consider the user's budget, preferences, and any mentioned places.
            Include mentioned places but also suggest alternatives.
            """
            
            user_prompt = f"""
            User preferences: {summary}
            
            Suggest destinations that match these preferences.
            """
            
            log_info("TripConsensus: calling structured LLM for place suggestions")
            
            try:
                candidates_obj = self.candidates_llm.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ])
                
                # Convert Pydantic models to dicts
                candidates = [candidate.model_dump() for candidate in candidates_obj.candidates]
                log_info("TripConsensus: structured candidates successful", candidate_count=len(candidates))
                
            except Exception as llm_err:
                log_error("TripConsensus: structured candidates LLM failed", error=str(llm_err))
                # Fallback to heuristic
                candidates = self._heuristic_candidates(summary)
                log_info("TripConsensus: using heuristic candidates fallback", candidate_count=len(candidates))
            
            log_info("TripConsensus: candidates generated", count=len(candidates))
            # Enrich candidates with images before returning
            try:
                candidates = self._add_images_to_candidates(candidates)
            except Exception as enrich_err:
                log_error("TripConsensus: enriching candidates with images failed", error=str(enrich_err))
            return {
                "candidates": candidates
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            log_error("TripConsensus: place_suggestion failed", error=str(e), traceback=error_details)
            return {
                "candidates": self._heuristic_candidates(state.get("summary", {}))
            }

    def _add_images_to_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attach an image URL to each candidate using Google Places photos when possible,
        else fall back to an Unsplash featured image. Adds both 'image' and 'image_url' keys for UI compatibility.
        """
        if not candidates:
            return candidates
        # Initialize client (safe if no API key)
        places_client: Optional[GooglePlacesClient] = None
        try:
            places_client = GooglePlacesClient()
        except Exception:
            places_client = None

        enriched: List[Dict[str, Any]] = []
        for c in candidates:
            name = c.get("place_name") or c.get("place") or c.get("name") or c.get("title")
            photo_url: Optional[str] = None
            if name and places_client and getattr(places_client, "api_key", None):
                try:
                    res = places_client.search_places(str(name))
                    if res:
                        photo_url = places_client.get_photo_media_url(res, max_width=640)
                except Exception:
                    photo_url = None

            if not photo_url and name:
                query = str(name).replace(" ", "+")
                photo_url = f"https://source.unsplash.com/featured/?{query}"

            if photo_url:
                enriched.append({**c, "image": photo_url, "image_url": photo_url})
            else:
                enriched.append(c)

        return enriched
    
    def _place_selection(self, state: TripConsensusState) -> Dict[str, Any]:
        """Intelligently select/reduce places based on user preferences and messages."""
        try:
            candidates = state.get("candidates", [])
            summary = state.get("summary", {})
            new_messages = state.get("new_messages", [])
            
            log_info("TripConsensus: place_selection starting", candidate_count=len(candidates))
            
            # If only one candidate, select it immediately
            if len(candidates) <= 1:
                selected_places = candidates
                log_info("TripConsensus: single/no candidate, selecting directly")
            else:
                # Use LLM to intelligently select places based on preferences
                system_prompt = """
                You are a travel consensus facilitator. Based on user messages and preferences, 
                select the most suitable travel destinations. Prioritize places that:
                1. Are explicitly mentioned positively in recent messages
                2. Match the user's stated preferences (budget, activities, etc.)
                3. Have strong consensus signals from multiple users
                
                If users are converging on specific places, select those. If there's still ambiguity,
                select 2-3 top candidates for further consideration.
                """
                
                messages_text = [msg.get("message", "") for msg in new_messages]
                user_prompt = f"""
                Current candidates: {candidates}
                User preferences: {summary}
                Recent messages: {messages_text}
                
                Select the most appropriate destinations based on user consensus and preferences.
                """
                
                log_info("TripConsensus: calling structured LLM for place selection")
                
                try:
                    selection_obj = self.selection_llm.invoke([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ])
                    
                    selected_places = [place.model_dump() for place in selection_obj.candidates]
                    log_info("TripConsensus: structured place selection successful", selected_count=len(selected_places))
                    
                except Exception as llm_err:
                    log_error("TripConsensus: place selection LLM failed", error=str(llm_err))
                    # Fallback: prefer mentioned places or take top candidates
                    selected_places = self._heuristic_place_selection(candidates, summary, new_messages)
                    log_info("TripConsensus: using heuristic place selection", selected_count=len(selected_places))
            
            # Determine status based on selection
            if len(selected_places) == 1:
                status = "converging"
            elif len(selected_places) > 1:
                status = "multiple_candidates"
            else:
                status = "no_candidates"
            
            log_info("TripConsensus: place selection complete", selected_count=len(selected_places), status=status)
            return {
                "selected_places": selected_places,
                "status": status
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            log_error("TripConsensus: place_selection failed", error=str(e), traceback=error_details)
            return {
                "selected_places": state.get("candidates", [])[:2],  # Fallback to top 2 candidates
                "status": "multiple_candidates"
            }
    
    def _heuristic_place_selection(self, candidates: List[Dict[str, Any]], summary: Dict[str, Any], new_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback heuristic place selection."""
        # Extract mentioned places from recent messages
        messages_text = " ".join([msg.get("message", "").lower() for msg in new_messages])
        
        # Score candidates based on mentions and preferences
        scored_candidates = []
        for candidate in candidates:
            place_name = candidate.get("place_name", "").lower()
            score = 0
            
            # Score based on mentions in messages
            if place_name in messages_text:
                score += 10
            
            # Score based on preferred places in summary
            preferred_places = [p.lower() for p in summary.get("preferred_places", [])]
            if place_name in preferred_places:
                score += 5
            
            scored_candidates.append((score, candidate))
        
        # Sort by score and return top candidates
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Return top 1-2 candidates
        if scored_candidates and scored_candidates[0][0] > 0:
            # If there's a clear winner, return just that
            if len(scored_candidates) == 1 or scored_candidates[0][0] > scored_candidates[1][0]:
                return [scored_candidates[0][1]]
            else:
                return [scored_candidates[0][1], scored_candidates[1][1]]
        else:
            # No clear preference, return top 2
            return [candidate for _, candidate in scored_candidates[:2]]
    
    def _heuristic_candidates(self, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback candidate generation."""
        preferred_places = summary.get("preferred_places", [])
        budget_max = summary.get("budget_max")
        
        def _make_candidate(place: str) -> Dict[str, Any]:
            return {
                "place_name": place.title(),
                "budget": "mid-range" if (budget_max and budget_max < 2000) else "luxury",
                "best_time": ["May", "September"],
                "why_it_matches": [
                    "Matches your preferences",
                    "Popular destination"
                ]
            }
        
        # Use preferred places or defaults
        base_places = preferred_places[:3] if preferred_places else ["rome", "paris", "barcelona"]
        return [_make_candidate(place) for place in base_places]
    
    def _consensus(self, state: TripConsensusState) -> Dict[str, Any]:
        """Generate consensus card if single place selected."""
        selected_places = state.get("selected_places", [])
        summary = state.get("summary", {})
        
        log_info("TripConsensus: consensus starting", selected_place_count=len(selected_places))
        
        if len(selected_places) == 1:
            # Generate consensus card using LLM
            chosen = selected_places[0]
            log_info("TripConsensus: single place selected, generating consensus card", chosen_place=chosen.get("place_name"))
            
            try:
                system_prompt = """
                Generate a detailed travel consensus card for a finalized destination.
                Generate realistic cost estimates based on the destination and budget category.
                """
                
                user_prompt = f"""
                Destination: {chosen['place_name']}
                Budget range: {chosen.get('budget', 'mid-range')}
                User summary: {summary}
                
                Generate a realistic consensus card with estimated costs.
                """
                
                log_info("TripConsensus: calling structured LLM for consensus card generation")
                
                consensus_card_obj = self.consensus_llm.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ])
                
                # Convert Pydantic model to dict
                consensus_card = consensus_card_obj.model_dump()
                log_info("TripConsensus: structured consensus card successful")
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                log_error("TripConsensus: consensus card generation failed", error=str(e), traceback=error_details)
                # Fallback consensus card
                consensus_card = {
                    "date": summary.get("start_date") or "2025-05-15",
                    "no_of_days": 5,
                    "weekdays_range": "Thu–Mon",
                    "accommodation_cost_per_person": 600,
                    "transportation_cost_per_person": 200,
                    "flight_cost_per_person": 800,
                    "places": [{
                        "place": chosen["place_name"],
                        "features": ", ".join(summary.get("travel_preferences", ["sightseeing"])),
                        "keywords": summary.get("travel_preferences", ["landmarks"])
                    }]
                }
                log_info("TripConsensus: using fallback consensus card")
            
            log_info("TripConsensus: consensus finalized", destination=chosen["place_name"])
            return {
                "status": "finalized",
                "consensus_card": consensus_card
            }
        
        else:
            log_info("TripConsensus: multiple places still selected", count=len(selected_places))
            return {
                "status": "multiple_candidates"
            }
    
    def process(self, init_state: TripConsensusState) -> Dict[str, Any]:
        """Process the consensus flow and return final state."""
        try:
            log_info("TripConsensus: starting process", trip_id=init_state.get("trip_id"))
            result = self.graph.invoke(init_state)
            log_info("TripConsensus: process completed", status=result.get("status"))
            return result
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            log_error("TripConsensus: process failed", error=str(e), traceback=error_details)
            return {
                "status": "error",
                "summary": {},
                "candidates": [],
                "consensus_card": None,
                "error_details": error_details
            }
