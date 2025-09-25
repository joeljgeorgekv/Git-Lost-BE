"""Chat service for handling chatbot interactions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import log_info
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat_schema import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
    ChatSessionWithMessages,
    ChatResponse
)


class ChatService:
    """Service for handling chatbot functionality."""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
    
    def create_session(self, user_id: Optional[int] = None) -> ChatSessionResponse:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        
        chat_session = ChatSession(
            user_id=user_id,
            session_id=session_id,
            title="New Chat"
        )
        
        self.db.add(chat_session)
        self.db.commit()
        self.db.refresh(chat_session)
        
        log_info("Created new chat session", session_id=session_id, user_id=user_id)
        
        return ChatSessionResponse(
            id=chat_session.id,
            session_id=chat_session.session_id,
            title=chat_session.title,
            created_at=chat_session.created_at,
            updated_at=chat_session.updated_at,
            message_count=0
        )
    
    def get_session(self, session_id: str) -> Optional[ChatSessionWithMessages]:
        """Get a chat session with all its messages."""
        chat_session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            return None
        
        messages = [
            ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                model=msg.model,
                tokens_used=msg.tokens_used,
                created_at=msg.created_at
            )
            for msg in chat_session.messages
        ]
        
        return ChatSessionWithMessages(
            id=chat_session.id,
            session_id=chat_session.session_id,
            title=chat_session.title,
            created_at=chat_session.created_at,
            updated_at=chat_session.updated_at,
            messages=messages
        )
    
    def get_user_sessions(self, user_id: int) -> List[ChatSessionResponse]:
        """Get all chat sessions for a user."""
        sessions = self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).all()
        
        return [
            ChatSessionResponse(
                id=session.id,
                session_id=session.session_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=len(session.messages)
            )
            for session in sessions
        ]
    
    def send_message(self, request: ChatMessageRequest, user_id: Optional[int] = None) -> ChatResponse:
        """Send a message and get AI response."""
        # Get or create session
        if request.session_id:
            chat_session = self.db.query(ChatSession).filter(
                ChatSession.session_id == request.session_id
            ).first()
            
            if not chat_session:
                raise ValueError("Session not found")
        else:
            # Create new session
            chat_session = ChatSession(
                user_id=user_id,
                session_id=str(uuid.uuid4()),
                title="New Chat"
            )
            self.db.add(chat_session)
            self.db.commit()
            self.db.refresh(chat_session)
        
        # Save user message
        user_message = ChatMessage(
            session_id=chat_session.id,
            role="user",
            content=request.message
        )
        self.db.add(user_message)
        self.db.commit()
        self.db.refresh(user_message)
        
        # Get conversation history
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        # Prepare messages for OpenAI
        openai_messages = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]
        
        # Add system message for better responses
        system_message = {
            "role": "system",
            "content": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses. Ask relevant follow-up questions when appropriate to better understand the user's needs."
        }
        openai_messages.insert(0, system_message)
        
        # Get AI response
        try:
            response = self.llm.invoke(openai_messages)
            ai_response = {
                "content": response.content,
                "model": request.model,
                "usage": {"total_tokens": response.response_metadata.get("token_usage", {}).get("total_tokens", 0)}
            }
            
            # Save AI response
            assistant_message = ChatMessage(
                session_id=chat_session.id,
                role="assistant",
                content=ai_response["content"],
                model=ai_response["model"],
                tokens_used=ai_response["usage"]["total_tokens"]
            )
            self.db.add(assistant_message)
            
            # Update session title if it's the first exchange
            if len(messages) == 1 and chat_session.title == "New Chat":
                # Generate a title from the first user message
                title_messages = [
                    {"role": "system", "content": "Generate a short, descriptive title (max 50 characters) for this conversation based on the user's first message."},
                    {"role": "user", "content": request.message}
                ]
                try:
                    title_response = self.llm.invoke(title_messages)
                    chat_session.title = title_response.content.strip()[:50]
                except Exception:
                    # Fallback to truncated user message
                    chat_session.title = request.message[:50]
            
            chat_session.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(assistant_message)
            
            log_info("Chat message processed", 
                    session_id=chat_session.session_id, 
                    user_message_id=user_message.id,
                    assistant_message_id=assistant_message.id)
            
            return ChatResponse(
                session=ChatSessionResponse(
                    id=chat_session.id,
                    session_id=chat_session.session_id,
                    title=chat_session.title,
                    created_at=chat_session.created_at,
                    updated_at=chat_session.updated_at,
                    message_count=len(chat_session.messages) + 1
                ),
                message=ChatMessageResponse(
                    id=user_message.id,
                    role=user_message.role,
                    content=user_message.content,
                    created_at=user_message.created_at
                ),
                response=ChatMessageResponse(
                    id=assistant_message.id,
                    role=assistant_message.role,
                    content=assistant_message.content,
                    model=assistant_message.model,
                    tokens_used=assistant_message.tokens_used,
                    created_at=assistant_message.created_at
                )
            )
            
        except Exception as e:
            log_info("Error processing chat message", error=str(e))
            raise Exception(f"Failed to process chat message: {str(e)}")
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages."""
        chat_session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            return False
        
        self.db.delete(chat_session)
        self.db.commit()
        
        log_info("Deleted chat session", session_id=session_id)
        return True
