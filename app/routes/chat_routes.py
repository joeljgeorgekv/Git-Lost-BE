from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.models.trip_chat import TripChatMessage
from app.schemas.trip_chat_schema import TripChatCreate, TripChatResponse
from app.schemas.consensus_chat_schema import ConsensusChatResponse
from app.models.trip_consensus import TripConsensus
from app.core.logger import log_info

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
            consensus=r.consensus
        )
        for r in rows
    ]

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

@router.post("/reach-consensus", response_model=ConsensusChatResponse)
def reach_consensus(trip_id: UUID, db: Session = Depends(get_db)) -> ConsensusChatResponse:
    """Process NEW messages for a trip using LangGraph consensus flow with persistent state.
    
    Flow:
    1. Fetch or create TripConsensus record for the trip
    2. Fetch NEW messages since last processing
    3. If new messages exist, run LangGraph to update consensus state
    4. Save updated state to database
    5. Mark processed messages as SUMMARIZED
    6. Return current consensus state
    """
    from app.langgraph.graphs.trip_consensus_graph import TripConsensusGraph
    from app.models.trip_consensus import TripConsensus
    from app.core.logger import log_info, log_error
    
    try:
        # 1) Fetch or create TripConsensus record
        log_info("reach_consensus: fetching consensus record", trip_id=str(trip_id))
        consensus_record = db.query(TripConsensus).filter(TripConsensus.trip_id == trip_id).first()
        
        if not consensus_record:
            # Create new consensus record - ensure only one per trip
            log_info("reach_consensus: creating new consensus record", trip_id=str(trip_id))
            consensus_record = TripConsensus(
                trip_id=trip_id,
                status="processing",
                iteration_count=0,
                summary={},
                candidates=[],
                consensus_card=None,
                last_processed_message_id=None
            )
            db.add(consensus_record)
            db.flush()  # Get the ID
            log_info("reach_consensus: created new consensus record", trip_id=str(trip_id), record_id=str(consensus_record.id))
        else:
            log_info("reach_consensus: found existing consensus record", 
                    trip_id=str(trip_id), 
                    current_status=consensus_record.status,
                    iteration_count=consensus_record.iteration_count)
        
        # 2) Fetch NEW messages since last processing
        log_info("reach_consensus: fetching NEW messages", trip_id=str(trip_id))
        query = db.query(TripChatMessage).filter(
            TripChatMessage.trip_id == trip_id,
            TripChatMessage.chat_status == TripChatMessage.ChatStatus.NEW,
        )
        
        # If we have a last processed message, only get newer ones
        if consensus_record.last_processed_message_id:
            log_info("reach_consensus: filtering messages after last processed", last_processed_id=str(consensus_record.last_processed_message_id))
            query = query.filter(TripChatMessage.id > consensus_record.last_processed_message_id)
        
        new_rows: list[TripChatMessage] = query.order_by(TripChatMessage.created_at.asc()).all()
        log_info("reach_consensus: found NEW messages", count=len(new_rows))
        
        # 3) Check if we have new messages to process
        if not new_rows:
            # No new messages, return existing state
            data = {
                "status": consensus_record.status,
                "trip_id": str(trip_id),
                "summary": consensus_record.summary or {},
                "candidates": consensus_record.candidates or [],
            }
            if consensus_record.consensus_card:
                data["consensus_card"] = consensus_record.consensus_card
            
            # Persist a consensus snapshot into trip_chat_messages for the client to consume
            try:
                system_msg = TripChatMessage(
                    trip_id=trip_id,
                    username="system",
                    message="consensus_update",
                )
                # Store the entire consensus payload for flexibility
                system_msg.consensus = data
                system_msg.chat_status = TripChatMessage.ChatStatus.SUMMARIZED
                db.add(system_msg)
                db.commit()
            except Exception:
                db.rollback()
                # Non-fatal: if persisting the snapshot fails, still return the response
                pass

            return ConsensusChatResponse(data=data)
        
        # 4) Prepare messages for LangGraph
        new_messages = [
            {
                "id": str(r.id),
                "username": r.username,
                "message": r.message,
                "created_at": r.created_at.isoformat(),
            }
            for r in new_rows
        ]
        
        # 5) Build LangGraph state from existing consensus + new messages
        graph = TripConsensusGraph()
        init_state = {
            "trip_id": str(trip_id),
            "new_messages": new_messages,
            "summary": consensus_record.summary,  # Start with existing summary
            "candidates": consensus_record.candidates or [],  # Start with existing candidates
            "selected_places": [],  # Will be populated by place_selection node
            "consensus_card": consensus_record.consensus_card,
            "status": "processing",
            "next_node": None,
            "iteration_count": consensus_record.iteration_count,  # Pass existing iteration count
        }
        
        # 6) Run LangGraph consensus flow
        result = graph.process(init_state)
        
        # 7) Update consensus record with new state
        if result.get("status") != "error":
            consensus_record.status = result.get("status", "processing")
            consensus_record.iteration_count = result.get("iteration_count", consensus_record.iteration_count)
            consensus_record.summary = result.get("summary", consensus_record.summary)
            consensus_record.candidates = result.get("candidates", consensus_record.candidates)
            consensus_record.consensus_card = result.get("consensus_card", consensus_record.consensus_card)
            
            # Track the last processed message
            if new_rows:
                consensus_record.last_processed_message_id = new_rows[-1].id
                
                # Mark messages as SUMMARIZED
                for r in new_rows:
                    r.chat_status = TripChatMessage.ChatStatus.SUMMARIZED
            
            db.commit()
            log_info("Updated consensus state", 
                    trip_id=str(trip_id), 
                    status=consensus_record.status,
                    iteration_count=consensus_record.iteration_count)
        
        # 8) Build response data
        data = {
            "status": consensus_record.status,
            "trip_id": str(trip_id),
            "summary": consensus_record.summary or {},
            "candidates": consensus_record.candidates or [],
        }
        
        if consensus_record.consensus_card:
            data["consensus_card"] = consensus_record.consensus_card

        try:
                system_msg = TripChatMessage(
                    trip_id=trip_id,
                    username="system",
                    message="consensus_update",
                )
                # Store the entire consensus payload for flexibility
                system_msg.consensus = data
                system_msg.chat_status = TripChatMessage.ChatStatus.SUMMARIZED
                db.add(system_msg)
                db.commit()
        except Exception:
            db.rollback()
            # Non-fatal: if persisting the snapshot fails, still return the response
            pass
        
        return ConsensusChatResponse(data=data)
        
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        log_error("reach_consensus failed", 
                 error=str(e), 
                 traceback=error_details,
                 trip_id=str(trip_id))
        
        return ConsensusChatResponse(data={
            "status": "error",
            "trip_id": str(trip_id),
            "summary": {},
            "candidates": [],
            "error": f"Processing failed: {str(e)}",
            "traceback": error_details
        })
