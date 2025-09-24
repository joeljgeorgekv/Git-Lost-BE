from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import log_info, log_error
from app.domain.user_domain import SignupRequest, LoginRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])  # Hackathon-simple auth
service = UserService()


@router.post("/signup")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        return service.signup(db, payload)
    except ValueError as e:
        if str(e) == "username_exists":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="signup failed")


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        return service.login(db, payload)
    except ValueError as e:
        if str(e) == "invalid_credentials":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="login failed")
