"""
FastAPI Backend for RAG Chatbot
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import uuid

# Import custom modules
from database import get_db, init_db, save_conversation, get_conversation_history, save_feedback, track_event
from rag_free import chat_with_rag

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Physical AI Book RAG Chatbot API",
    description="Retrieval-Augmented Generation chatbot for Physical AI & Humanoid Robotics book",
    version="1.0.0"
)

# CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "https://umeradnan7106.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    chapter_context: Optional[str] = None

class ChatSelectionRequest(BaseModel):
    message: str
    selected_text: str
    session_id: Optional[str] = None
    chapter_context: Optional[str] = None

class FeedbackRequest(BaseModel):
    conversation_id: str
    rating: int  # 1 or -1
    comment: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    conversation_id: str
    session_id: str

class HealthResponse(BaseModel):
    status: str
    version: str
    message: str

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization failed: {e}")

# Health check endpoint
@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        message="RAG Chatbot API is running!"
    )

# Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Main chat endpoint"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get conversation history
        history = get_conversation_history(db, session_id, limit=5)
        session_history = [
            {"question": h.user_message, "answer": h.bot_response}
            for h in reversed(history)
        ]
        
        # Get RAG response
        rag_result = chat_with_rag(
            question=request.message,
            session_history=session_history,
            chapter_filter=request.chapter_context
        )
        
        # Save to database
        conversation = save_conversation(
            db=db,
            session_id=session_id,
            user_message=request.message,
            bot_response=rag_result["answer"],
            chapter_context=request.chapter_context,
            sources=rag_result["sources"]
        )
        
        # Track analytics
        track_event(
            db=db,
            event_type="chat",
            session_id=session_id,
            metadata={"chapter": request.chapter_context}
        )
        
        return ChatResponse(
            answer=rag_result["answer"],
            sources=rag_result["sources"],
            conversation_id=str(conversation.id),
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

# Chat with selected text endpoint
@app.post("/api/chat-selection", response_model=ChatResponse)
async def chat_selection(
    request: ChatSelectionRequest,
    db: Session = Depends(get_db)
):
    """Chat endpoint for selected text"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get conversation history
        history = get_conversation_history(db, session_id, limit=5)
        session_history = [
            {"question": h.user_message, "answer": h.bot_response}
            for h in reversed(history)
        ]
        
        # Get RAG response with selected text
        rag_result = chat_with_rag(
            question=request.message,
            session_history=session_history,
            selected_text=request.selected_text,
            chapter_filter=request.chapter_context
        )
        
        # Save to database
        conversation = save_conversation(
            db=db,
            session_id=session_id,
            user_message=request.message,
            bot_response=rag_result["answer"],
            chapter_context=request.chapter_context,
            selected_text=request.selected_text,
            sources=rag_result["sources"]
        )
        
        # Track analytics
        track_event(
            db=db,
            event_type="selection_chat",
            session_id=session_id,
            metadata={
                "chapter": request.chapter_context,
                "selection_length": len(request.selected_text)
            }
        )
        
        return ChatResponse(
            answer=rag_result["answer"],
            sources=rag_result["sources"],
            conversation_id=str(conversation.id),
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Selection chat error: {str(e)}")

# Feedback endpoint
@app.post("/api/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit feedback for a conversation"""
    try:
        feedback = save_feedback(
            db=db,
            conversation_id=request.conversation_id,
            rating=request.rating,
            comment=request.comment
        )
        
        return {"message": "Feedback saved successfully", "feedback_id": str(feedback.id)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback error: {str(e)}")

# Get conversation history endpoint
@app.get("/api/history/{session_id}")
async def get_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get conversation history for a session"""
    try:
        history = get_conversation_history(db, session_id, limit=20)
        
        return {
            "session_id": session_id,
            "conversations": [
                {
                    "id": str(h.id),
                    "message": h.user_message,
                    "response": h.bot_response,
                    "timestamp": h.timestamp.isoformat(),
                    "chapter": h.chapter_context
                }
                for h in reversed(history)
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
