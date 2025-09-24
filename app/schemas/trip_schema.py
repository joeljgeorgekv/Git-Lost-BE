from __future__ import annotations

import uuid
from pydantic import BaseModel


class TripCreate(BaseModel):
    trip_name: str


class TripRead(BaseModel):
    id: uuid.UUID
    trip_name: str

    model_config = {"from_attributes": True}
