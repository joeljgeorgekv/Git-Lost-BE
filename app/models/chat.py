"""Chat models for storing conversation data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.models import Base


class ChatSession(Base):
    """Model for storing chat sessions."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional user association
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=True)  # Optional session title
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to messages
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Model for storing individual chat messages."""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    model = Column(String(100), nullable=True)  # AI model used for response
    tokens_used = Column(Integer, nullable=True)  # Token usage for AI responses
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to session
    session = relationship("ChatSession", back_populates="messages")
