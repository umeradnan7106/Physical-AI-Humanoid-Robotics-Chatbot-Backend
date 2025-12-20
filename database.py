"""
Database connection and operations
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Conversation, Feedback, Analytics
import os
from dotenv import load_dotenv
import json
from typing import Optional, List, Dict
from datetime import datetime

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Conversation CRUD operations
def save_conversation(
    db: Session,
    session_id: str,
    user_message: str,
    bot_response: str,
    chapter_context: Optional[str] = None,
    selected_text: Optional[str] = None,
    sources: Optional[List[Dict]] = None
) -> Conversation:
    """Save a conversation to database"""
    conversation = Conversation(
        session_id=session_id,
        user_message=user_message,
        bot_response=bot_response,
        chapter_context=chapter_context,
        selected_text=selected_text,
        sources=json.dumps(sources) if sources else None
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

def get_conversation_history(db: Session, session_id: str, limit: int = 10) -> List[Conversation]:
    """Get conversation history for a session"""
    return db.query(Conversation)\
        .filter(Conversation.session_id == session_id)\
        .order_by(Conversation.timestamp.desc())\
        .limit(limit)\
        .all()

# Feedback operations
def save_feedback(
    db: Session,
    conversation_id: str,
    rating: int,
    comment: Optional[str] = None
) -> Feedback:
    """Save user feedback"""
    feedback = Feedback(
        conversation_id=conversation_id,
        rating=rating,
        comment=comment
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback

# Analytics operations
def track_event(
    db: Session,
    event_type: str,
    session_id: str,
    metadata: Optional[Dict] = None
):
    """Track analytics event"""
    analytics = Analytics(
        event_type=event_type,
        session_id=session_id,
        event_metadata=json.dumps(metadata) if metadata else None
    )
    db.add(analytics)
    db.commit()
