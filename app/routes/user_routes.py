from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.core.logger import log_info, log_error


class SignupRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str

router = APIRouter(prefix="/users", tags=["users"])  # Hackathon-simple auth


@router.post("/signup")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    log_info("signup request", username=payload.username)
    # Check if user exists
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing is not None:
        log_error("signup failed - username exists", username=payload.username)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
    # Create user (PLAINTEXT password for hackathon only)
    user = User(username=payload.username, password=payload.password)
    db.add(user)
    db.commit()
    log_info("signup success", username=payload.username)
    return {"message": "signup successful", "username": payload.username}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    log_info("login request", username=payload.username)
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or user.password != payload.password:
        log_error("login failed", username=payload.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    # Return a fake token to mimic auth flow for the hackathon
    log_info("login success", username=payload.username)
    return {"access_token": f"fake-token-{payload.username}", "token_type": "bearer"}
