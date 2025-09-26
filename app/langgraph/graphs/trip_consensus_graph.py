from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
from datetime import datetime, timedelta

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
    origin_place: Optional[str] = Field(None, description="Origin city/place where the trip starts from")
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
    origin_place: Optional[str] = Field(None, description="Origin city/place where the trip starts from")


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
    iteration_count: int  # Track iterations to force convergence after 3 rounds


class TripConsensusGraph:
    """LangGraph for trip planning consensus flow with Summarizer, Place Suggestion, and Consensus nodes."""
    
    def __init__(self) -> None:
        base_llm = ChatOpenAI(
            model="gpt-5", 
            temperature=0.2, 
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
        sg.add_node("save_consensus", self._save_consensus)  # New node to save consensus to DB
        
        # Define edges - simplified flow without unnecessary exits
        sg.add_edge("check_messages", "summarizer")
        sg.add_edge("summarizer", "place_suggestion")
        sg.add_edge("place_suggestion", "place_selection")
        
        sg.add_conditional_edges(
            "place_selection",
            self._route_after_selection,
            {
                "consensus": "consensus",
                "end": "save_consensus"  # Always save state before ending
            }
        )
        
        sg.add_edge("consensus", "save_consensus")  # Save consensus after generation
        sg.add_edge("save_consensus", END)  # End after saving
        
        # Set entry point
        sg.set_entry_point("check_messages")
        
        return sg.compile()
    
    # Routing functions for conditional edges
    
    def _route_after_selection(self, state: TripConsensusState) -> str:
        """Route after place selection - key logic for consensus."""
        selected_places = state.get("selected_places", [])
        iteration_count = state.get("iteration_count", 0)
        
        # Force convergence after 3 iterations to prevent infinite loops
        if iteration_count >= 3:
            if selected_places:
                # Force convergence to top candidate
                log_info("TripConsensus: max iterations reached, forcing convergence", 
                        iteration_count=iteration_count, place_count=len(selected_places))
                return "consensus"
            else:
                log_info("TripConsensus: max iterations reached, no candidates, ending")
                return "end"
        
        if not selected_places:
            log_info("TripConsensus: no places selected, ending")
            return "end"
        elif len(selected_places) == 1:
            log_info("TripConsensus: single place selected, proceeding to consensus")
            return "consensus"
        else:
            # Multiple places - end with multiple candidates status
            log_info("TripConsensus: multiple places selected, ending with multiple candidates", 
                    place_count=len(selected_places), iteration_count=iteration_count)
            return "end"
    
    def _check_messages(self, state: TripConsensusState) -> Dict[str, Any]:
        """Check if there are new messages to process."""
        new_messages = state.get("new_messages", [])
        
        # Initialize iteration counter if not present
        iteration_count = state.get("iteration_count", 0)
        
        if not new_messages:
            log_info("TripConsensus: no new messages, proceeding with existing data")
            return {
                "status": "no_new_messages",
                "iteration_count": iteration_count
            }
        else:
            log_info("TripConsensus: new messages found, starting processing", message_count=len(new_messages))
            return {
                "status": "processing",
                "iteration_count": iteration_count + 1
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
        
        # Extract origin place
        origin_hints = [
            "from new york", "from nyc", "from london", "from paris", "from tokyo",
            "from los angeles", "from chicago", "from boston", "from miami",
            "from san francisco", "from seattle", "from denver", "from atlanta"
        ]
        origin_place = None
        for hint in origin_hints:
            if hint in text_lower:
                origin_place = hint.replace("from ", "").upper()
                break
        
        return {
            "budget_min": budget_min,
            "budget_max": budget_max,
            "start_date": start_date,
            "end_date": end_date,
            "origin_place": origin_place,
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
                # Use more lenient heuristic selection to converge faster
                selected_places = self._heuristic_place_selection(candidates, summary, new_messages)
                log_info("TripConsensus: using heuristic place selection", selected_count=len(selected_places))
            
            # More lenient status determination to help convergence
            if len(selected_places) == 1:
                status = "converging"
            elif len(selected_places) == 2:
                # If we have 2 candidates and there are positive signals, pick the top one
                messages_text = " ".join([msg.get("message", "").lower() for msg in new_messages])
                
                # Check for strong positive signals (focus, prefer, let's go with, etc.)
                convergence_signals = ["focus on", "let's go with", "prefer", "choose", "pick", "decide on"]
                has_strong_signal = any(signal in messages_text for signal in convergence_signals)
                
                if has_strong_signal:
                    # Force convergence to top candidate
                    selected_places = selected_places[:1]
                    status = "converging"
                    log_info("TripConsensus: detected convergence signal, selecting top candidate")
                else:
                    status = "multiple_candidates"
            elif len(selected_places) > 2:
                # Too many candidates, reduce to top 2
                selected_places = selected_places[:2]
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
                "selected_places": state.get("candidates", [])[:1],  # Fallback to top 1 candidate for faster convergence
                "status": "converging"
            }
    
    def _heuristic_place_selection(self, candidates: List[Dict[str, Any]], summary: Dict[str, Any], new_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback heuristic place selection with lenient scoring."""
        # Extract mentioned places from recent messages
        messages_text = " ".join([msg.get("message", "").lower() for msg in new_messages])
        
        # Score candidates based on mentions and preferences
        scored_candidates = []
        for candidate in candidates:
            place_name = candidate.get("place_name", "").lower()
            score = 1  # Base score for all candidates to avoid zero scores
            
            # Score based on exact mentions in messages
            if place_name in messages_text:
                score += 10
            
            # Score based on partial matches (e.g., "rome" matches "rome, italy")
            place_words = place_name.split()
            for word in place_words:
                if len(word) > 3 and word in messages_text:  # Avoid short words like "in", "to"
                    score += 5
            
            # Score based on preferred places in summary
            preferred_places = [p.lower() for p in summary.get("preferred_places", [])]
            for pref in preferred_places:
                if pref in place_name or place_name in pref:
                    score += 8
            
            # Score based on travel preferences matching
            travel_prefs = [p.lower() for p in summary.get("travel_preferences", [])]
            candidate_reasons = [r.lower() for r in candidate.get("why_it_matches", [])]
            for pref in travel_prefs:
                for reason in candidate_reasons:
                    if pref in reason:
                        score += 3
            
            # Bonus for budget match
            candidate_budget = candidate.get("budget", "").lower()
            if candidate_budget:
                budget_max = summary.get("budget_max", 0)
                if budget_max:
                    if (budget_max < 1000 and "budget" in candidate_budget) or \
                       (1000 <= budget_max <= 2500 and "mid-range" in candidate_budget) or \
                       (budget_max > 2500 and "luxury" in candidate_budget):
                        score += 4
            
            scored_candidates.append((score, candidate))
        
        # Sort by score and return top candidates
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # More lenient selection logic
        if not scored_candidates:
            return []
        
        # If top candidate has significantly higher score, return just that
        if len(scored_candidates) == 1:
            return [scored_candidates[0][1]]
        
        top_score = scored_candidates[0][0]
        second_score = scored_candidates[1][0] if len(scored_candidates) > 1 else 0
        
        # If top candidate has 2x or more score than second, converge to it
        if top_score >= second_score * 2 and top_score > 5:
            return [scored_candidates[0][1]]
        
        # Otherwise return top 2 for further consideration
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
        iteration_count = state.get("iteration_count", 0)
        
        log_info("TripConsensus: consensus starting", selected_place_count=len(selected_places), iteration_count=iteration_count)
        
        # Force convergence after 3 iterations - pick the first available place
        if iteration_count >= 3 and selected_places:
            chosen = selected_places[0]
            log_info("TripConsensus: forced convergence due to max iterations", chosen_place=chosen.get("place_name"))
        elif len(selected_places) == 1:
            chosen = selected_places[0]
        else:
            # This shouldn't happen due to routing logic, but handle gracefully
            log_error("TripConsensus: consensus called with multiple places", place_count=len(selected_places))
            return {
                "status": "multiple_candidates"
            }
        
        # Generate consensus card using LLM
        log_info("TripConsensus: generating consensus card", chosen_place=chosen.get("place_name"))
        
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
            # Normalize to ensure dates/days/weekday range and origin/places consistency
            consensus_card = self._normalize_consensus_card(chosen, summary, consensus_card)
            log_info("TripConsensus: structured consensus card successful")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            log_error("TripConsensus: consensus card generation failed", error=str(e), traceback=error_details)
            # Fallback consensus card
            consensus_card = {
                "date": summary.get("start_date") or "2025-05-15",
                # no_of_days and weekdays_range will be normalized below
                "no_of_days": 3,
                "weekdays_range": "Fri–Sun",
                "accommodation_cost_per_person": 600,
                "transportation_cost_per_person": 200,
                "flight_cost_per_person": 800,
                "places": [{
                    "place": chosen["place_name"],
                    "features": ", ".join(summary.get("travel_preferences", ["sightseeing"])),
                    "keywords": summary.get("travel_preferences", ["landmarks"])
                }],
                "origin_place": summary.get("origin_place")
            }
            consensus_card = self._normalize_consensus_card(chosen, summary, consensus_card)
            log_info("TripConsensus: using fallback consensus card")
        
        log_info("TripConsensus: consensus finalized", destination=chosen["place_name"])
        return {
            "status": "finalized",
            "consensus_card": consensus_card
        }

    def _normalize_consensus_card(self, chosen: Dict[str, Any], summary: Dict[str, Any], card: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize consensus card to ensure internally consistent fields.
        - date aligns with summary.start_date when present
        - no_of_days and weekdays_range are computed from (start_date, end_date)
        - ensure places contains the chosen destination with minimal fields
        - propagate origin_place from summary when missing
        - clamp costs to non-negative integers
        """
        try:
            start_str = (summary or {}).get("start_date") or card.get("date")
            end_str = (summary or {}).get("end_date")
            # Parse dates when possible
            start_dt = None
            end_dt = None
            if start_str:
                try:
                    start_dt = datetime.fromisoformat(start_str)
                except Exception:
                    start_dt = None
            if end_str:
                try:
                    end_dt = datetime.fromisoformat(end_str)
                except Exception:
                    end_dt = None

            # Compute days and weekday range
            if start_dt:
                if end_dt and end_dt >= start_dt:
                    days = (end_dt - start_dt).days + 1  # inclusive day count
                    end_for_range = end_dt
                else:
                    # fall back to existing no_of_days or minimum 1
                    days = max(int(card.get("no_of_days") or 1), 1)
                    end_for_range = start_dt + timedelta(days=days - 1)

                # Update fields
                card["date"] = start_dt.date().isoformat()
                card["no_of_days"] = days
                card["weekdays_range"] = f"{start_dt.strftime('%a')}–{end_for_range.strftime('%a')}"

            # Ensure places list
            places = card.get("places")
            if not isinstance(places, list) or len(places) == 0:
                card["places"] = [{
                    "place": chosen.get("place_name", ""),
                    "features": ", ".join((summary or {}).get("travel_preferences", [])) or "",
                    "keywords": (summary or {}).get("travel_preferences", []) or []
                }]
            else:
                # Ensure first item has the chosen place name
                card["places"][0].setdefault("place", chosen.get("place_name", ""))

            # Propagate origin_place
            if not card.get("origin_place"):
                origin = (summary or {}).get("origin_place")
                if origin:
                    card["origin_place"] = origin

            # Clamp costs to non-negative ints
            for k in ("accommodation_cost_per_person", "transportation_cost_per_person", "flight_cost_per_person"):
                try:
                    v = int(card.get(k) if card.get(k) is not None else 0)
                    card[k] = max(v, 0)
                except Exception:
                    card[k] = 0

            # Ensure minimal correctness of no_of_days
            try:
                nd = int(card.get("no_of_days", 1))
                card["no_of_days"] = max(nd, 1)
            except Exception:
                card["no_of_days"] = 1

        except Exception as norm_err:
            # If normalization fails, log and return original card
            log_error("TripConsensus: consensus card normalization failed", error=str(norm_err))
        return card
    
    def _save_consensus(self, state: TripConsensusState) -> Dict[str, Any]:
        """Save the final consensus state to the database."""
        try:
            from app.models.trip_consensus import TripConsensus
            from app.core.database import get_db
            
            trip_id = state.get("trip_id")
            log_info("TripConsensus: saving consensus to database", trip_id=trip_id)
            
            # Get database session
            db = next(get_db())
            
            try:
                # Find the consensus record for this trip
                consensus_record = db.query(TripConsensus).filter(
                    TripConsensus.trip_id == trip_id
                ).first()
                
                if consensus_record:
                    # Update the existing record with final state
                    consensus_record.status = state.get("status", "processing")
                    consensus_record.iteration_count = state.get("iteration_count", 0)
                    consensus_record.summary = state.get("summary", {})
                    consensus_record.candidates = state.get("candidates", [])
                    consensus_record.consensus_card = state.get("consensus_card")
                    
                    db.commit()
                    log_info("TripConsensus: successfully saved consensus to database", 
                            trip_id=trip_id, 
                            status=consensus_record.status,
                            iteration_count=consensus_record.iteration_count)
                else:
                    log_error("TripConsensus: consensus record not found for trip", trip_id=trip_id)
                    
            except Exception as db_error:
                db.rollback()
                log_error("TripConsensus: database error while saving consensus", 
                         trip_id=trip_id, error=str(db_error))
            finally:
                db.close()
                
        except Exception as e:
            log_error("TripConsensus: failed to save consensus", trip_id=state.get("trip_id"), error=str(e))
        
        # Return the state unchanged - this is just a side effect
        return {}
    
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
