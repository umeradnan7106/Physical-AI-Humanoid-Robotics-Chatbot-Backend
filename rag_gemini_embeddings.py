"""
RAG Logic with Google Gemini Embeddings (100% Cloud-based, FREE, Lightweight)
"""
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-1.5-flash')  # Stable FREE model with 1500 requests/day

# Initialize Qdrant
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "physical_ai_book")

def create_collection():
    """Create Qdrant collection for Google embeddings (768 dims)"""
    try:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        print(f"Created collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"Collection already exists or error: {e}")

def generate_embedding(text: str) -> List[float]:
    """Generate FREE embedding using Google Gemini Embedding API"""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Embedding error: {e}")
        # Fallback to simple hash-based vector if API fails
        return [0.0] * 768

def upsert_document(chunk_id: str, text: str, metadata: Dict):
    """Insert document into Qdrant"""
    vector = generate_embedding(text)

    point = PointStruct(
        id=chunk_id,
        vector=vector,
        payload={
            "text": text,
            "chapter": metadata.get("chapter", ""),
            "section": metadata.get("section", ""),
            "file_path": metadata.get("file_path", "")
        }
    )

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[point]
    )

def search_similar_chunks(query: str, limit: int = 3, chapter_filter: Optional[str] = None) -> List[Dict]:
    """Search for similar chunks in Qdrant"""
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

    try:
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
                "text": result.payload.get("text", ""),
                "chapter": result.payload.get("chapter", ""),
                "section": result.payload.get("section", ""),
                "score": result.score,
                "file_path": result.payload.get("file_path", "")
            })

        return chunks
    except Exception as e:
        print(f"Search error: {e}")
        return []

def chat_with_rag(
    question: str,
    session_history: List[Dict] = None,
    selected_text: Optional[str] = None,
    chapter_filter: Optional[str] = None
) -> Dict:
    """
    Chat with RAG using Google Gemini (100% FREE, Cloud-based)
    """
    # Search for relevant chunks
    chunks = search_similar_chunks(question, limit=3, chapter_filter=chapter_filter)

    # Build context
    context = "\n\n".join([
        f"[Chapter: {chunk['chapter']}]\n{chunk['text']}"
        for chunk in chunks
    ])

    # Build conversation history
    history_text = ""
    if session_history:
        for msg in session_history[-3:]:  # Last 3 exchanges
            history_text += f"\nUser: {msg['question']}\nAssistant: {msg['answer']}\n"

    # Build prompt
    if selected_text:
        prompt = f"""You are a helpful AI assistant for a Physical AI & Humanoid Robotics textbook.

The user selected this text:
"{selected_text}"

And asked: {question}

Relevant context from the book:
{context}

Previous conversation:
{history_text}

Provide a clear, educational answer focusing on the selected text and the question. Format your response with:
- Clear explanations
- Bullet points for lists
- **Bold** for important terms
- Proper paragraphs

Answer:"""
    else:
        prompt = f"""You are a helpful AI assistant for a Physical AI & Humanoid Robotics textbook.

User question: {question}

Relevant context from the book:
{context}

Previous conversation:
{history_text}

Provide a clear, educational answer based on the context. Format your response with:
- Clear explanations
- Bullet points for lists
- **Bold** for important terms
- Proper paragraphs

If the context doesn't contain enough information, say so and provide general knowledge about the topic.

Answer:"""

    try:
        # Generate response with Gemini
        response = gemini_model.generate_content(prompt)
        answer = response.text

        # Format sources
        sources = [
            {
                "chapter": chunk["chapter"],
                "section": chunk["section"],
                "score": round(chunk["score"], 3)
            }
            for chunk in chunks
        ]

        return {
            "answer": answer,
            "sources": sources
        }

    except Exception as e:
        print(f"Error generating response: {e}")
        return {
            "answer": f"Sorry, I encountered an error while generating the response. Please try again. Error: {str(e)}",
            "sources": []
        }
