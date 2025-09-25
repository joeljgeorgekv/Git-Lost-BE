from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.itinerary_service import ItineraryService
from app.domain.itinerary_domain import ItenaryCreateRequest, Itinerary, ItineraryUpdateRequest, PlaceInfo

router = APIRouter(prefix="/itineraries", tags=["itineraries"])

_service = ItineraryService()


@router.post("", response_model=List[PlaceInfo])
async def create_itinerary(payload: ItenaryCreateRequest) -> List[PlaceInfo]:
    """Create an itinerary using AI and return a list of PlaceInfo entries."""
    # Always use AI via graph (with safe fallback inside graph)
    return _service.create_itinerary_places(payload)


@router.get("", response_model=List[Itinerary])
async def list_itineraries() -> List[Itinerary]:
    """List all created itineraries (in-memory)."""
    return _service.list_itineraries()


@router.get("/{itinerary_id}", response_model=Itinerary)
async def get_itinerary(itinerary_id: str) -> Itinerary:
    it = _service.get_itinerary(itinerary_id)
    if not it:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return it


@router.patch("/{itinerary_id}", response_model=Itinerary)
async def update_itinerary(itinerary_id: str, payload: ItineraryUpdateRequest) -> Itinerary:
    it = _service.update_itinerary(itinerary_id, title=payload.title, notes=payload.notes)
    if not it:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return it


@router.delete("/{itinerary_id}")
async def delete_itinerary(itinerary_id: str) -> dict:
    ok = _service.delete_itinerary(itinerary_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return {"deleted": True, "id": itinerary_id}
