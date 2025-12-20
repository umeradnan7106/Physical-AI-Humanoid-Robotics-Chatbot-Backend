"""
RAG Logic with FREE alternatives (Google Gemini + Sentence Transformers)
"""
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize local embedding model (FREE!)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

# Initialize Qdrant
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "physical_ai_book")

def create_collection():
    """Create Qdrant collection for free embeddings (384 dims)"""
    try:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"✅ Created collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"Collection already exists or error: {e}")

def generate_embedding(text: str) -> List[float]:
    """Generate FREE embedding using Sentence Transformers"""
    embedding = embedding_model.encode(text)
    return embedding.tolist()

def upsert_document(chunk_id: str, text: str, metadata: Dict):
    """Insert document into Qdrant"""
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
    """Search for similar chunks"""
    query_vector = generate_embedding(query)

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

    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        query_filter=search_filter,
        with_payload=True
    ).points
    
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
    """Generate answer using FREE Google Gemini"""
    
    # Build context
    context = "\n\n".join([
        f"[From {chunk['chapter']}]\n{chunk['text']}"
        for chunk in context_chunks
    ])
    
    # Build prompt
    prompt = f"""You are an expert AI assistant for the "Physical AI & Humanoid Robotics" educational book.

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
    
    if selected_text:
        prompt += f"\nUser selected this text from the book:\n\"{selected_text}\"\n\nAnswer their question specifically about this selection.\n"
    
    # Add conversation history
    if conversation_history:
        prompt += "\nPrevious conversation:\n"
        for msg in conversation_history[-3:]:
            prompt += f"User: {msg['question']}\nAssistant: {msg['answer']}\n"
    
    prompt += f"\nUser Question: {question}\n\nAnswer:"
    
    # Generate response with Gemini (FREE!)
    try:
        response = gemini_model.generate_content(prompt)
        answer = response.text
    except Exception as e:
        answer = f"Sorry, I encountered an error: {str(e)}"
    
    return {
        "answer": answer,
        "sources": context_chunks,
        "model": "gemini-2.5-flash"
    }

def chat_with_rag(
    question: str,
    session_history: Optional[List[Dict]] = None,
    selected_text: Optional[str] = None,
    chapter_filter: Optional[str] = None
) -> Dict:
    """Main RAG function with FREE models"""
    
    search_query = f"{selected_text}\n{question}" if selected_text else question
    
    chunks = search_similar_chunks(
        query=search_query,
        limit=3,
        chapter_filter=chapter_filter
    )
    
    result = generate_answer(
        question=question,
        context_chunks=chunks,
        conversation_history=session_history,
        selected_text=selected_text
    )
    
    return result
