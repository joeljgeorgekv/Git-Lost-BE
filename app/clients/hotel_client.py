from __future__ import annotations

import os
from typing import List, Dict, Any, Optional
import requests

from app.core.logger import log_info, log_error


class HotelClient:
    """Client for hotel booking APIs (mock implementation for MVP)."""
    
    def __init__(self):
        # In production, use real APIs like Booking.com, Expedia, etc.
        self.api_key = os.getenv("HOTEL_API_KEY")
        self.base_url = "https://api.example-hotel-service.com"  # Mock URL
    
    def search_hotels(
        self, 
        destination: str, 
        check_in: str, 
        check_out: str,
        guests: int = 2,
        budget_range: str = "mid-range"
    ) -> List[Dict[str, Any]]:
        """Search for hotels in destination."""
        
        # Mock hotel data based on destination and budget
        if destination.lower() == "bali":
            hotels = self._get_bali_hotels(budget_range)
        elif destination.lower() == "phuket":
            hotels = self._get_phuket_hotels(budget_range)
        else:
            hotels = self._get_generic_hotels(destination, budget_range)
        
        log_info("Hotel search completed (mock)", destination=destination, results=len(hotels))
        return hotels
    
    def _get_bali_hotels(self, budget_range: str) -> List[Dict[str, Any]]:
        """Get Bali-specific hotel options."""
        if budget_range == "budget":
            return [
                {
                    "name": "Kuta Beach Hostel",
                    "location": "Kuta",
                    "price_per_night_usd": 25,
                    "rating": 4.1,
                    "amenities": ["WiFi", "Pool", "Breakfast"],
                    "why_matches": "Budget-friendly with great location near beach",
                    "booking_link": "https://booking.example.com/hotels/kuta-beach-hostel",
                    "photo_url": "https://example.com/photos/kuta-hostel.jpg"
                }
            ]
        elif budget_range == "luxury":
            return [
                {
                    "name": "The Mulia Resort",
                    "location": "Nusa Dua",
                    "price_per_night_usd": 450,
                    "rating": 4.8,
                    "amenities": ["Spa", "Private Beach", "Multiple Pools", "Fine Dining"],
                    "why_matches": "Luxury beachfront resort with world-class amenities",
                    "booking_link": "https://booking.example.com/hotels/mulia-resort",
                    "photo_url": "https://example.com/photos/mulia-resort.jpg"
                }
            ]
        else:  # mid-range
            return [
                {
                    "name": "Ubud Village Hotel",
                    "location": "Ubud",
                    "price_per_night_usd": 85,
                    "rating": 4.4,
                    "amenities": ["Pool", "Spa", "Restaurant", "Cultural Tours"],
                    "why_matches": "Perfect for cultural exploration with modern comfort",
                    "booking_link": "https://booking.example.com/hotels/ubud-village",
                    "photo_url": "https://example.com/photos/ubud-village.jpg"
                },
                {
                    "name": "Seminyak Beach Resort",
                    "location": "Seminyak",
                    "price_per_night_usd": 120,
                    "rating": 4.5,
                    "amenities": ["Beach Access", "Pool", "Rooftop Bar", "Spa"],
                    "why_matches": "Great for beach lovers with vibrant nightlife nearby",
                    "booking_link": "https://booking.example.com/hotels/seminyak-beach",
                    "photo_url": "https://example.com/photos/seminyak-beach.jpg"
                }
            ]
    
    def _get_phuket_hotels(self, budget_range: str) -> List[Dict[str, Any]]:
        """Get Phuket-specific hotel options."""
        base_hotels = [
            {
                "name": "Patong Beach Hotel",
                "location": "Patong",
                "price_per_night_usd": 95,
                "rating": 4.3,
                "amenities": ["Beach Access", "Pool", "Restaurant", "Nightlife"],
                "why_matches": "Central location with easy access to beaches and entertainment",
                "booking_link": "https://booking.example.com/hotels/patong-beach",
                "photo_url": "https://example.com/photos/patong-beach.jpg"
            }
        ]
        return base_hotels
    
    def _get_generic_hotels(self, destination: str, budget_range: str) -> List[Dict[str, Any]]:
        """Get generic hotel options for any destination."""
        price_map = {
            "budget": 40,
            "mid-range": 90,
            "luxury": 250
        }
        
        return [
            {
                "name": f"{destination} Central Hotel",
                "location": "City Center",
                "price_per_night_usd": price_map.get(budget_range, 90),
                "rating": 4.2,
                "amenities": ["WiFi", "Restaurant", "Gym"],
                "why_matches": f"Well-located hotel in {destination} with good amenities",
                "booking_link": f"https://booking.example.com/hotels/{destination.lower()}-central",
                "photo_url": f"https://example.com/photos/{destination.lower()}-hotel.jpg"
            }
        ]
    
    def get_hotel_details(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific hotel."""
        # Mock implementation
        return {
            "detailed_description": "Detailed hotel information...",
            "facilities": ["Pool", "Spa", "Restaurant", "WiFi"],
            "policies": {
                "check_in": "15:00",
                "check_out": "11:00",
                "cancellation": "Free cancellation up to 24 hours before check-in"
            }
        }
