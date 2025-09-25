from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models.trip_chat import TripChatMessage
from app.schemas.trip_chat_schema import TripChatCreate, TripChatResponse

router = APIRouter(prefix="/chats", tags=["chats"])

@router.get("/{trip_id}", response_model=list[TripChatResponse])
def get_chats(trip_id: UUID, db: Session = Depends(get_db)) -> list[TripChatResponse]:
    """Get all chat messages for a specific trip, ordered by time."""
    rows = (
        db.query(TripChatMessage)
        .filter(TripChatMessage.trip_id == trip_id)
        .order_by(TripChatMessage.created_at.asc())
        .all()
    )
    return [
        TripChatResponse(
            id=r.id,
            trip_id=r.trip_id,
            username=r.username,
            message=r.message,
            time=r.created_at,
        )
        for r in rows
    ]

@router.post("/", response_model=TripChatResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=TripChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(payload: TripChatCreate, db: Session = Depends(get_db)) -> TripChatResponse:
    """Create a chat message linked to a trip.

    Fields saved:
    - trip_id
    - username
    - message
    - created_at (server time by default; if client provides `time`, we use it)
    """
    try:
        chat = TripChatMessage(
            trip_id=payload.trip_id,
            username=payload.username,
            message=payload.message,
        )

        # Allow optional client-provided timestamp
        if payload.time is not None:
            chat.created_at = payload.time

        db.add(chat)
        db.commit()
        db.refresh(chat)

        return TripChatResponse(
            id=chat.id,
            trip_id=chat.trip_id,
            username=chat.username,
            message=chat.message,
            time=chat.created_at,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed_to_create_chat_message: {str(e)}",
        )

# Placeholder removed; use POST /chats/ defined above
