from __future__ import annotations

from pydantic import BaseModel


class SignupRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str
