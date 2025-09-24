from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


class SignupRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str

router = APIRouter(prefix="/users", tags=["users"])  # Hackathon-simple auth


@router.post("/signup")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
    # Create user (PLAINTEXT password for hackathon only)
    user = User(username=payload.username, password=payload.password)
    db.add(user)
    db.commit()
    return {"message": "signup successful", "username": payload.username}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or user.password != payload.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    # Return a fake token to mimic auth flow for the hackathon
    return {"access_token": f"fake-token-{payload.username}", "token_type": "bearer"}
