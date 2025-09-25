from __future__ import annotations

from typing import List, Dict, Any, Optional
import requests

from app.core.logger import log_info, log_error
from app.core.config import settings


class GooglePlacesClient:
    """Client for Google Places API integration."""
    
    def __init__(self):
        # Read via centralized settings (loaded from .env)
        self.api_key = settings.google_places_api_key
        if not self.api_key:
            log_error("Google Places API key not found in environment")
        # Legacy base URL (v0)
        self.base_url = "https://maps.googleapis.com/maps/api"
        # New Places API v1 base URL
        self.base_url_v1 = "https://places.googleapis.com/v1"
    
    def search_places(self, query: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for places using Google Places API.
        Uses v1 places:searchText endpoint and returns the raw 'places' array.
        """
        if not self.api_key:
            return []
        
        try:
            url = f"{self.base_url_v1}/places:searchText"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                # Request fields we need (photos and display name)
                "X-Goog-FieldMask": "places.photos"
            }
            payload: Dict[str, Any] = {
                "textQuery": query
            }
            # Optional: could add location bias in v1 via 'locationBias' if needed
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()

            

            data = response.json()
            name = None
            places = data.get("places", [])
            if places:
                photos = places[0].get("photos", [])
                if photos:
                    name = photos[0].get("name")

            log_info("Google Places v1 search completed", name=name)
            return name
            
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

    def get_photo_media_url(self, photo_name: str, max_width: int = 640) -> Optional[str]:
        """Return a media URL for a photo object from either v1 (has 'name') or legacy (has 'photo_reference')."""
        if not self.api_key or not photo_name:
            return None

        name = photo_name
        if name:
            # GET https://places.googleapis.com/v1/{name}/media?key=API_KEY&maxWidthPx=...
            return f"{self.base_url_v1}/{name}/media?maxWidthPx={max_width}&key={self.api_key}"
        return None
