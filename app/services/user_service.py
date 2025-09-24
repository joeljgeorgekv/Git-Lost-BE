from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.logger import log_info, log_error
from app.domain.user_domain import SignupRequest, LoginRequest

class UserService:
    """Encapsulates user-related business logic (MVP)."""

    def __init__(self) -> None:
        pass

    def signup(self, db: Session, payload: SignupRequest) -> dict:
        log_info("signup request", username=payload.username)
        existing: Optional[User] = db.query(User).filter(User.username == payload.username).first()
        if existing is not None:
            log_error("signup failed - username exists", username=payload.username)
            raise ValueError("username_exists")

        user = User(username=payload.username, password=payload.password)
        db.add(user)
        db.commit()
        log_info("signup success", username=payload.username)
        return {"message": "signup successful", "username": payload.username}

    def login(self, db: Session, payload: LoginRequest) -> dict:
        log_info("login request", username=payload.username)
        user: Optional[User] = db.query(User).filter(User.username == payload.username).first()
        if user is None or user.password != payload.password:
            log_error("login failed", username=payload.username)
            raise ValueError("invalid_credentials")
        log_info("login success", username=payload.username)
        return {"access_token": f"fake-token-{payload.username}", "token_type": "bearer"}
