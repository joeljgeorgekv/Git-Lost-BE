from __future__ import annotations

import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI

from app.clients.google_places_client import GooglePlacesClient
from app.core.config import settings
from app.core.logger import log_info, log_error
from app.domain.travel_planning_domain import TripOverview, AreaPlan


class TripPlanningAgent:
    """Agent responsible for creating initial trip overview and area plans."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
        self.places_client = GooglePlacesClient()
    
    def create_trip_overview(
        self, 
        destination: str, 
        messages: List[Dict[str, Any]], 
        summary: str
    ) -> TripOverview:
        """Create an initial trip overview for the selected destination."""
        
        system_prompt = f"""
        You are a travel planning expert. Create a trip overview for {destination}.
        
        Based on the chat messages, create a trip plan with:
        1. A catchy trip name (e.g., "Bali Long Weekend", "Phuket Beach Escape")
        2. Suggested dates based on their preferences
        3. Number of days (typically 3-7 days)
        4. Different areas/regions to explore within the destination
        
        Return JSON in this format:
        {{
            "trip_name": "Catchy Trip Name",
            "destination": "{destination}",
            "dates": "Suggested date range",
            "num_days": number_of_days,
            "day_names": ["Day1", "Day2", "Day3"],
            "areas": [
                {{
                    "area_name": "Area/Region Name with theme",
                    "what_to_see": ["attraction1", "attraction2", "attraction3"],
                    "keywords": ["keyword1", "keyword2", "keyword3"],
                    "estimated_days": 1.5
                }}
            ]
        }}
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
            
            chat_context = json.dumps({"messages": messages[-10:]})
            ai_messages.append({
                "role": "user",
                "content": f"Create trip overview based on: {chat_context}"
            })
            
            response = self.llm.invoke(ai_messages)
            trip_data = json.loads(response.content)
            
            # Convert to domain objects
            areas = [
                AreaPlan(
                    area_name=area["area_name"],
                    what_to_see=area["what_to_see"],
                    keywords=area["keywords"],
                    estimated_days=area["estimated_days"]
                )
                for area in trip_data["areas"]
            ]
            
            trip_overview = TripOverview(
                trip_name=trip_data["trip_name"],
                destination=trip_data["destination"],
                dates=trip_data["dates"],
                num_days=trip_data["num_days"],
                day_names=trip_data["day_names"],
                areas=areas
            )
            
            log_info("Trip overview created", destination=destination, trip_name=trip_overview.trip_name)
            return trip_overview
            
        except Exception as e:
            log_error("Failed to create trip overview", destination=destination, error=str(e))
            return self._get_fallback_trip_overview(destination)
    
    def _get_fallback_trip_overview(self, destination: str) -> TripOverview:
        """Return fallback trip overview if AI fails."""
        
        # Generate basic trip based on destination
        if destination.lower() == "bali":
            return TripOverview(
                trip_name="Bali Cultural & Beach Escape",
                destination="Bali",
                dates="April 15-18, 2025",
                num_days=4,
                day_names=["Thursday", "Friday", "Saturday", "Sunday"],
                areas=[
                    AreaPlan(
                        area_name="Ubud Cultural Journey",
                        what_to_see=["Rice Terraces", "Monkey Forest", "Traditional Markets", "Temples"],
                        keywords=["Culture", "Nature", "Temples", "Art"],
                        estimated_days=1.5
                    ),
                    AreaPlan(
                        area_name="Seminyak Beach Relaxation",
                        what_to_see=["Beach Clubs", "Sunset Views", "Shopping", "Spa"],
                        keywords=["Beach", "Sunset", "Dining", "Relaxation"],
                        estimated_days=2.5
                    )
                ]
            )
        elif destination.lower() == "phuket":
            return TripOverview(
                trip_name="Phuket Island Adventure",
                destination="Phuket",
                dates="March 20-24, 2025",
                num_days=5,
                day_names=["Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                areas=[
                    AreaPlan(
                        area_name="Patong Beach Fun",
                        what_to_see=["Patong Beach", "Bangla Road", "Water Sports", "Beach Bars"],
                        keywords=["Beach", "Nightlife", "Water Sports", "Entertainment"],
                        estimated_days=2.0
                    ),
                    AreaPlan(
                        area_name="Island Hopping Adventure",
                        what_to_see=["Phi Phi Islands", "James Bond Island", "Snorkeling", "Boat Tours"],
                        keywords=["Islands", "Adventure", "Snorkeling", "Boat Tours"],
                        estimated_days=3.0
                    )
                ]
            )
        else:
            return TripOverview(
                trip_name=f"{destination} Discovery Trip",
                destination=destination,
                dates="TBD",
                num_days=4,
                day_names=["Day 1", "Day 2", "Day 3", "Day 4"],
                areas=[
                    AreaPlan(
                        area_name=f"{destination} Highlights",
                        what_to_see=["Main Attractions", "Local Culture", "Food Scene"],
                        keywords=["Culture", "Food", "Sightseeing"],
                        estimated_days=4.0
                    )
                ]
            )
