"""
RAG (Retrieval-Augmented Generation) Logic
"""
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import hashlib

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "physical_ai_book")
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

def create_collection():
    """Create Qdrant collection if it doesn't exist"""
    try:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
        print(f"✅ Created collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"Collection already exists or error: {e}")

def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text using OpenAI"""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding

def upsert_document(
    chunk_id: str,
    text: str,
    metadata: Dict
):
    """Insert or update a document chunk in Qdrant"""
    vector = generate_embedding(text)
    
    point = PointStruct(
        id=chunk_id,
        vector=vector,
        payload={
            "text": text,
            "chapter": metadata.get("chapter", ""),
            "url": metadata.get("url", ""),
            "module": metadata.get("module", ""),
            "title": metadata.get("title", "")
        }
    )
    
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[point]
    )

def search_similar_chunks(
    query: str,
    limit: int = 3,
    chapter_filter: Optional[str] = None
) -> List[Dict]:
    """Search for similar chunks in Qdrant"""
    query_vector = generate_embedding(query)
    
    # Build filter if chapter specified
    search_filter = None
    if chapter_filter:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="chapter",
                    match=MatchValue(value=chapter_filter)
                )
            ]
        )
    
    results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit,
        query_filter=search_filter,
        with_payload=True
    )
    
    chunks = []
    for result in results:
        chunks.append({
            "text": result.payload["text"],
            "chapter": result.payload["chapter"],
            "url": result.payload["url"],
            "score": result.score,
            "title": result.payload.get("title", "")
        })
    
    return chunks

def generate_answer(
    question: str,
    context_chunks: List[Dict],
    conversation_history: Optional[List[Dict]] = None,
    selected_text: Optional[str] = None
) -> Dict:
    """Generate answer using OpenAI with retrieved context"""
    
    # Build context from chunks
    context = "\n\n".join([
        f"[From {chunk['chapter']}]\n{chunk['text']}"
        for chunk in context_chunks
    ])
    
    # System prompt
    system_prompt = f"""You are an expert AI assistant for the "Physical AI & Humanoid Robotics" educational book.

Your role:
1. Answer questions based ONLY on the provided book context
2. Be precise, technical, and educational
3. If the answer isn't in the context, say "I don't have information about that in the book"
4. Reference specific chapters when helpful
5. Use code examples when relevant
6. Be concise but complete

Book Context:
{context}
"""
    
    # Add selected text context if provided
    if selected_text:
        system_prompt += f"\n\nUser selected this text from the book:\n\"{selected_text}\"\n\nAnswer their question specifically about this selection."
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history[-5:]:  # Last 5 messages
            messages.append({"role": "user", "content": msg["question"]})
            messages.append({"role": "assistant", "content": msg["answer"]})
    
    # Add current question
    messages.append({"role": "user", "content": question})
    
    # Generate response
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=800
    )
    
    answer = response.choices[0].message.content
    
    return {
        "answer": answer,
        "sources": context_chunks,
        "model": CHAT_MODEL
    }

def chat_with_rag(
    question: str,
    session_history: Optional[List[Dict]] = None,
    selected_text: Optional[str] = None,
    chapter_filter: Optional[str] = None
) -> Dict:
    """Main RAG function - retrieve and generate"""
    
    # If selected text provided, use it as additional context
    search_query = f"{selected_text}\n{question}" if selected_text else question
    
    # Search for relevant chunks
    chunks = search_similar_chunks(
        query=search_query,
        limit=3,
        chapter_filter=chapter_filter
    )
    
    # Generate answer
    result = generate_answer(
        question=question,
        context_chunks=chunks,
        conversation_history=session_history,
        selected_text=selected_text
    )
    
    return result
