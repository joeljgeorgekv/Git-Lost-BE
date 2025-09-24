from __future__ import annotations

import uuid
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str


class UserRead(BaseModel):
    id: uuid.UUID
    username: str

    model_config = {"from_attributes": True}
