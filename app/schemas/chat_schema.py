"""Pydantic schemas for chat API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    """Request schema for sending a chat message."""
    
    message: str
    session_id: Optional[str] = None
    model: Optional[str] = "gpt-3.5-turbo"


class ChatMessageResponse(BaseModel):
    """Response schema for chat message."""
    
    id: int
    role: str
    content: str
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: datetime


class ChatSessionResponse(BaseModel):
    """Response schema for chat session."""
    
    id: int
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int


class ChatSessionWithMessages(BaseModel):
    """Response schema for chat session with messages."""
    
    id: int
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse]


class ChatResponse(BaseModel):
    """Complete response schema for chat interaction."""
    
    session: ChatSessionResponse
    message: ChatMessageResponse
    response: ChatMessageResponse
