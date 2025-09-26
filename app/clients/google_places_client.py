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
                # Request fields we need (include id and location for future use)
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.photos"
            }
            payload: Dict[str, Any] = {
                "textQuery": query
            }
            # Optional: could add location bias in v1 via 'locationBias' if needed
            response = requests.post(url, headers=headers, json=payload, timeout=3)
            response.raise_for_status()

            data = response.json()
            places = data.get("places", [])
            log_info("Google Places v1 search completed", count=len(places))
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
            
            response = requests.get(url, params=params, timeout=3)
            response.raise_for_status()
            
            data = response.json()
            place_details = data.get("result", {})
            
            log_info("Google Places details retrieved", place_id=place_id)
            return place_details
            
        except Exception as e:
            log_error("Google Places details API error", error=str(e), place_id=place_id)
            return None

    def resolve_place(self, query: str) -> Optional[Dict[str, Any]]:
        """Resolve a free-text place query to a dict with formattedAddress and lat/lng if available.

        Returns:
            {
              'name': str,                # display name text if present
              'formattedAddress': str|None,
              'lat': float|None,
              'lng': float|None,
            } or None if not found
        """
        results = self.search_places(query)
        name = None
        addr = None
        lat = None
        lng = None
        if results:
            top = results[0]
            name = (top.get('displayName') or {}).get('text')
            addr = top.get('formattedAddress')
            try:
                latlng = top.get('location', {}).get('latLng') or {}
                lat = latlng.get('latitude')
                lng = latlng.get('longitude')
            except Exception:
                pass
        # Fallback to OpenStreetMap Nominatim if we still don't have coordinates
        if lat is None or lng is None:
            try:
                import requests
                from urllib.parse import urlencode
                url = f"https://nominatim.openstreetmap.org/search?{urlencode({'q': query, 'format': 'json', 'limit': 1})}"
                headers = {"User-Agent": "git-lost-be/itinerary (contact: dev@example.com)"}
                resp = requests.get(url, headers=headers, timeout=3)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list) and data:
                    lat = float(data[0].get('lat'))
                    lng = float(data[0].get('lon'))
            except Exception:
                pass
        return {
            'name': name or query,
            'formattedAddress': addr,
            'lat': lat,
            'lng': lng,
        }

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compute great-circle distance between two points (km)."""
        from math import radians, sin, cos, asin, sqrt
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return R * c
    
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
            
            response = requests.get(url, params=params, timeout=3)
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

    def get_first_photo_media_url_for_query(self, query: str, max_width: int = 640) -> Optional[str]:
        """Search and return the first photo media URL for a given query, if available."""
        places = self.search_places(query)
        if not places:
            return None
        photos = places[0].get("photos", [])
        if not photos:
            return None
        first_photo_name = photos[0].get("name")
        return self.get_photo_media_url(first_photo_name, max_width=max_width)

    def get_map_link(self, place_name_or_address: str) -> str:
        """Construct a Google Maps search link for a place."""
        from urllib.parse import urlencode
        return f"https://www.google.com/maps/search/?api=1&{urlencode({'query': place_name_or_address})}"

    def get_distance_between(self, origin: str, destination: str) -> Optional[str]:
        """Return human-readable distance between two places using Distance Matrix (first element)."""
        # Resolve origin/destination into formatted addresses for higher accuracy
        def _resolve(q: str) -> str:
            try:
                results = self.search_places(q)
                if results:
                    addr = results[0].get("formattedAddress")
                    if addr:
                        return addr
                    # fallback to displayName if address missing
                    dn = results[0].get("displayName", {}).get("text")
                    if dn:
                        return dn
            except Exception:
                pass
            return q

        resolved_origin = _resolve(origin)
        resolved_destination = _resolve(destination)

        data = self.get_distance_matrix([resolved_origin], [resolved_destination])
        try:
            rows = data.get("rows", [])
            if rows and rows[0].get("elements"):
                elem = rows[0]["elements"][0]
                if elem.get("status") == "OK" and elem.get("distance"):
                    return elem["distance"]["text"]
        except Exception:
            pass

        # Fallback: compute haversine distance if we can resolve coordinates
        try:
            o = self.resolve_place(origin)
            d = self.resolve_place(destination)
            if o and d and o.get("lat") and o.get("lng") and d.get("lat") and d.get("lng"):
                km = self.haversine_km(o["lat"], o["lng"], d["lat"], d["lng"])
                return f"{km:.1f} km"
        except Exception:
            pass
        return None
