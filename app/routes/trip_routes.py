from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/trips", tags=["trips"])  # Intentionally empty for MVP
