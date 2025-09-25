from __future__ import annotations

import json
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI

from app.clients.google_places_client import GooglePlacesClient
from app.core.config import settings
from app.core.logger import log_info, log_error
from app.domain.travel_planning_domain import DetailedItineraryDay, Activity, TripOverview


class ItineraryAgent:
    """Agent responsible for creating detailed day-by-day itineraries with verified distances."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )
        self.places_client = GooglePlacesClient()
    
    def create_detailed_itinerary(
        self, 
        trip_overview: TripOverview,
        selected_hotel: str,
        messages: List[Dict[str, Any]]
    ) -> List[DetailedItineraryDay]:
        """Create a detailed day-by-day itinerary with verified distances."""
        
        system_prompt = f"""
        You are an expert travel itinerary planner. Create a detailed day-by-day itinerary for {trip_overview.destination}.
        
        Trip Details:
        - Destination: {trip_overview.destination}
        - Duration: {trip_overview.num_days} days
        - Areas to cover: {[area.area_name for area in trip_overview.areas]}
        - Hotel: {selected_hotel}
        
        Create a realistic itinerary with:
        1. Specific times for each activity
        2. Realistic travel times between locations
        3. Mix of must-see attractions and local experiences
        4. Proper meal breaks
        5. Estimated costs for each activity
        
        Return JSON array with this structure:
        [
            {{
                "day": 1,
                "day_name": "Thursday",
                "date": "April 15, 2025",
                "activities": [
                    {{
                        "time": "9:00 AM",
                        "name": "Activity Name",
                        "location": "Specific Location",
                        "duration": "2 hours",
                        "description": "What you'll do and see",
                        "estimated_cost_usd": 25,
                        "distance_from_previous": "15 minutes by car",
                        "transport_method": "Private car"
                    }}
                ],
                "estimated_budget_usd": 150
            }}
        ]
        """
        
        try:
            # Prepare messages for AI
            ai_messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add context from chat messages
            chat_context = json.dumps({
                "messages": messages[-5:],  # Recent preferences
                "trip_overview": trip_overview.dict()
            })
            ai_messages.append({
                "role": "user",
                "content": f"Create detailed itinerary based on: {chat_context}"
            })
            
            response = self.llm.invoke(ai_messages)
            itinerary_data = json.loads(response.content)
            
            # Convert to domain objects and verify distances
            detailed_days = []
            for day_data in itinerary_data:
                activities = []
                for activity_data in day_data["activities"]:
                    activity = Activity(
                        time=activity_data["time"],
                        name=activity_data["name"],
                        location=activity_data["location"],
                        duration=activity_data["duration"],
                        description=activity_data["description"],
                        estimated_cost_usd=activity_data["estimated_cost_usd"],
                        distance_from_previous=activity_data.get("distance_from_previous"),
                        transport_method=activity_data.get("transport_method")
                    )
                    activities.append(activity)
                
                day = DetailedItineraryDay(
                    day=day_data["day"],
                    day_name=day_data["day_name"],
                    date=day_data["date"],
                    activities=activities,
                    estimated_budget_usd=day_data["estimated_budget_usd"]
                )
                detailed_days.append(day)
            
            # Verify and optimize distances
            detailed_days = self._verify_distances(detailed_days)
            
            log_info("Detailed itinerary created", days=len(detailed_days), destination=trip_overview.destination)
            return detailed_days
            
        except Exception as e:
            log_error("Failed to create detailed itinerary", error=str(e), destination=trip_overview.destination)
            return self._get_fallback_itinerary(trip_overview)
    
    def _verify_distances(self, days: List[DetailedItineraryDay]) -> List[DetailedItineraryDay]:
        """Verify and update distances between activities using Google Maps."""
        
        for day in days:
            if len(day.activities) < 2:
                continue
            
            try:
                # Get locations for distance calculation
                locations = [activity.location for activity in day.activities]
                
                # Use Google Distance Matrix API
                distance_data = self.places_client.get_distance_matrix(
                    origins=locations[:-1],  # All except last
                    destinations=locations[1:]  # All except first
                )
                
                if distance_data and "rows" in distance_data:
                    for i, activity in enumerate(day.activities[1:], 1):
                        try:
                            element = distance_data["rows"][i-1]["elements"][0]
                            if element["status"] == "OK":
                                duration = element["duration"]["text"]
                                distance = element["distance"]["text"]
                                activity.distance_from_previous = f"{distance} ({duration})"
                        except (KeyError, IndexError):
                            pass
                            
            except Exception as e:
                log_error("Failed to verify distances for day", day=day.day, error=str(e))
        
        return days
    
    def _get_fallback_itinerary(self, trip_overview: TripOverview) -> List[DetailedItineraryDay]:
        """Return fallback itinerary if AI fails."""
        
        if trip_overview.destination.lower() == "bali":
            return [
                DetailedItineraryDay(
                    day=1,
                    day_name="Thursday",
                    date="April 15, 2025",
                    activities=[
                        Activity(
                            time="9:00 AM",
                            name="Arrival and Hotel Check-in",
                            location="Hotel",
                            duration="2 hours",
                            description="Arrive, check-in, and freshen up",
                            estimated_cost_usd=0,
                            transport_method="Airport transfer"
                        ),
                        Activity(
                            time="12:00 PM",
                            name="Lunch at Local Warung",
                            location="Ubud Center",
                            duration="1 hour",
                            description="Try authentic Balinese cuisine",
                            estimated_cost_usd=15,
                            distance_from_previous="30 minutes by car",
                            transport_method="Private car"
                        ),
                        Activity(
                            time="2:00 PM",
                            name="Tegallalang Rice Terraces",
                            location="Tegallalang",
                            duration="2 hours",
                            description="Explore famous rice terraces and take photos",
                            estimated_cost_usd=10,
                            distance_from_previous="20 minutes by car",
                            transport_method="Private car"
                        )
                    ],
                    estimated_budget_usd=75
                )
            ]
        else:
            return [
                DetailedItineraryDay(
                    day=1,
                    day_name="Day 1",
                    date="TBD",
                    activities=[
                        Activity(
                            time="9:00 AM",
                            name="City Exploration",
                            location=f"{trip_overview.destination} Center",
                            duration="3 hours",
                            description="Explore the main attractions",
                            estimated_cost_usd=50,
                            transport_method="Walking"
                        )
                    ],
                    estimated_budget_usd=100
                )
            ]
