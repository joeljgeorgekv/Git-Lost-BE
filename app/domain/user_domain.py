from __future__ import annotations

import uuid
from pydantic import BaseModel


class SignupRequest(BaseModel):
    username: str
    password: str


class SignupResponse(BaseModel):
    user_id: uuid.UUID
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: uuid.UUID
    username: str
