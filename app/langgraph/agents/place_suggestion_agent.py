from __future__ import annotations

import json
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI

from app.clients.google_places_client import GooglePlacesClient
from app.core.logger import log_info, log_error
from app.domain.travel_planning_domain import PlaceOption
from app.core.config import settings

class PlaceSuggestionAgent:
    """Agent responsible for suggesting travel destinations based on chat context."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
        self.places_client = GooglePlacesClient()
    
    def suggest_places(self, messages: List[Dict[str, Any]], summary: str) -> List[PlaceOption]:
        """Analyze chat messages and suggest suitable destinations."""
        
        # Extract preferences using AI
        system_prompt = """
        You are a travel destination expert. Analyze the chat messages and extract travel preferences.
        
        Based on the conversation, suggest 3-5 destinations that would be perfect for this group.
        Consider factors like:
        - Budget mentioned
        - Activities they're interested in
        - Time of year they want to travel
        - Group size and dynamics
        - Any specific preferences mentioned
        
        Return a JSON array of destinations with this structure:
        [
            {
                "place": "Destination Name",
                "country": "Country",
                "best_months": ["Month1", "Month2", "Month3"],
                "why_matches": "Explanation of why this fits their preferences",
                "avg_budget_usd": estimated_budget_per_person,
                "highlights": ["attraction1", "attraction2", "attraction3"]
            }
        ]
        """
        
        try:
            # Prepare messages for AI
            ai_messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            if summary:
                ai_messages.append({
                    "role": "system", 
                    "content": f"Previous conversation summary: {summary}"
                })
            
            # Add recent messages
            chat_context = json.dumps({"messages": messages[-10:]})  # Last 10 messages
            ai_messages.append({
                "role": "user",
                "content": f"Analyze these chat messages and suggest destinations: {chat_context}"
            })
            
            response = self.llm.invoke(ai_messages)
            
            # Parse AI response
            suggestions_data = json.loads(response.content)
            
            place_options = []
            for suggestion in suggestions_data:
                # Enhance with Google Places data if available
                photo_url = self._get_destination_photo(suggestion["place"])
                
                place_option = PlaceOption(
                    place=suggestion["place"],
                    country=suggestion["country"],
                    best_months=suggestion["best_months"],
                    why_matches=suggestion["why_matches"],
                    avg_budget_usd=suggestion["avg_budget_usd"],
                    highlights=suggestion["highlights"],
                    photo_url=photo_url
                )
                place_options.append(place_option)
            
            log_info("Place suggestions generated", count=len(place_options))
            return place_options
            
        except Exception as e:
            log_error("Failed to generate place suggestions", error=str(e))
            # Return fallback suggestions
            return self._get_fallback_suggestions()
    
    def _get_destination_photo(self, destination: str) -> str:
        """Get a photo for the destination using Google Places."""
        try:
            places = self.places_client.search_places(f"{destination} tourist attractions")
            if places and len(places) > 0:
                place = places[0]
                if "photos" in place and len(place["photos"]) > 0:
                    photo_ref = place["photos"][0]["photo_reference"]
                    return self.places_client.get_photo_url(photo_ref)
        except Exception as e:
            log_error("Failed to get destination photo", destination=destination, error=str(e))
        
        return f"https://images.unsplash.com/search/photos/{destination.lower().replace(' ', '-')}"
    
    def _get_fallback_suggestions(self) -> List[PlaceOption]:
        """Return fallback suggestions if AI fails."""
        return [
            PlaceOption(
                place="Bali",
                country="Indonesia",
                best_months=["April", "May", "June", "September", "October"],
                why_matches="Perfect blend of culture, beaches, and adventure activities",
                avg_budget_usd=800,
                highlights=["Temples", "Rice Terraces", "Beaches", "Volcanoes"],
                photo_url="https://images.unsplash.com/search/photos/bali"
            ),
            PlaceOption(
                place="Phuket",
                country="Thailand",
                best_months=["November", "December", "January", "February", "March"],
                why_matches="Beautiful beaches with vibrant nightlife and great food",
                avg_budget_usd=600,
                highlights=["Beaches", "Island Hopping", "Thai Cuisine", "Nightlife"],
                photo_url="https://images.unsplash.com/search/photos/phuket"
            ),
            PlaceOption(
                place="Goa",
                country="India",
                best_months=["November", "December", "January", "February"],
                why_matches="Relaxed beach destination with Portuguese heritage",
                avg_budget_usd=400,
                highlights=["Beaches", "Portuguese Architecture", "Seafood", "Nightlife"],
                photo_url="https://images.unsplash.com/search/photos/goa"
            )
        ]
