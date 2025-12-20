"""
Database models for RAG Chatbot
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    """Store all chat conversations"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    chapter_context = Column(String(500))
    selected_text = Column(Text)  # For text selection feature
    sources = Column(Text)  # JSON string of source chunks
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Conversation {self.id}>"

class Feedback(Base):
    """Store user feedback on responses"""
    __tablename__ = "feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'))
    rating = Column(Integer)  # 1 for thumbs up, -1 for thumbs down
    comment = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Feedback {self.id} rating={self.rating}>"

class Analytics(Base):
    """Track usage analytics"""
    __tablename__ = "analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100))  # chat, selection_chat, feedback
    session_id = Column(String(255), index=True)
    event_metadata = Column(Text)  # JSON string (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    timestamp = Column(DateTime, default=datetime.utcnow)
