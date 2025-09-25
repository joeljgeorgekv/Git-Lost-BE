from __future__ import annotations

import os
from typing import List, Dict, Any, Optional
import requests

from app.core.logger import log_info, log_error


class GooglePlacesClient:
    """Client for Google Places API integration."""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            log_error("Google Places API key not found in environment")
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    def search_places(self, query: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for places using Google Places API."""
        if not self.api_key:
            return []
        
        try:
            url = f"{self.base_url}/place/textsearch/json"
            params = {
                "query": query,
                "key": self.api_key
            }
            
            if location:
                params["location"] = location
                params["radius"] = 50000  # 50km radius
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            places = data.get("results", [])
            
            log_info("Google Places search completed", query=query, results_count=len(places))
            return places
            
        except Exception as e:
            log_error("Google Places API error", error=str(e), query=query)
            return []
    
    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific place."""
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}/place/details/json"
            params = {
                "place_id": place_id,
                "key": self.api_key,
                "fields": "name,formatted_address,rating,price_level,photos,opening_hours,website,international_phone_number"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            place_details = data.get("result", {})
            
            log_info("Google Places details retrieved", place_id=place_id)
            return place_details
            
        except Exception as e:
            log_error("Google Places details API error", error=str(e), place_id=place_id)
            return None
    
    def get_distance_matrix(self, origins: List[str], destinations: List[str]) -> Optional[Dict[str, Any]]:
        """Get distance and duration between multiple origins and destinations."""
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}/distancematrix/json"
            params = {
                "origins": "|".join(origins),
                "destinations": "|".join(destinations),
                "key": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            log_info("Distance matrix retrieved", origins_count=len(origins), destinations_count=len(destinations))
            return data
            
        except Exception as e:
            log_error("Distance Matrix API error", error=str(e))
            return None
    
    def get_photo_url(self, photo_reference: str, max_width: int = 400) -> Optional[str]:
        """Get photo URL from photo reference."""
        if not self.api_key or not photo_reference:
            return None
        
        return f"{self.base_url}/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={self.api_key}"
