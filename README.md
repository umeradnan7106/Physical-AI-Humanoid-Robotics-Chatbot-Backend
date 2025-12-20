# RAG Chatbot Backend

AI-powered chatbot for Physical AI & Humanoid Robotics book using RAG (Retrieval-Augmented Generation).

## 🎯 Two Versions Available

### ✅ **FREE Version** (RECOMMENDED - $0/month)
Uses 100% FREE services:
- **AI Model**: Google Gemini Pro (FREE tier)
- **Embeddings**: Sentence Transformers (Local, FREE)
- **Vector DB**: Qdrant Cloud (1GB FREE)
- **SQL DB**: Neon Serverless Postgres (3GB FREE)

**Files**: `rag_free.py`, `ingest_free.py`, `requirements_free.txt`

### 💵 **OpenAI Version** (~$5-10/month)
Uses OpenAI API (paid):
- **AI Model**: OpenAI GPT-4o-mini
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: Qdrant Cloud
- **SQL DB**: Neon Serverless Postgres

**Files**: `rag.py`, `ingest.py`, `requirements.txt`

---

## Features (Both Versions)

- **Retrieval-Augmented Generation**: Answers based on book content
- **Selected Text Chat**: Ask questions about highlighted text
- **Conversation History**: Persistent chat sessions
- **Vector Search**: Semantic search using Qdrant
- **PostgreSQL Storage**: Chat history and analytics

## Current Configuration

**✅ ACTIVE**: FREE Version (Google Gemini + Sentence Transformers)

The `main.py` is currently configured to use the FREE version (`rag_free.py`)

## Setup Instructions (FREE Version)

📖 **Full Setup Guide**: See `../FREE_VERSION_SETUP.md` for complete step-by-step instructions!

### Quick Start:

### 1. Install Dependencies (FREE version)

```bash
cd backend
pip install -r requirements_free.txt
```

**Note**: First run downloads the embedding model (~80MB), subsequent runs are instant!

### 2. Configure Environment Variables

Create `.env` file:

```bash
cp .env.example .env
```

Fill in your **FREE** API keys:

```env
# Google Gemini (FREE - get from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=your-google-api-key-here

# Qdrant Cloud (FREE 1GB)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-key

# Neon Postgres (FREE 3GB)
DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require
```

### 3. Initialize Database

```bash
python main.py
```

This will create all necessary tables.

### 4. Ingest Book Content (FREE Version)

```bash
python ingest_free.py
```

This will:
- Process all markdown files
- Generate FREE embeddings using Sentence Transformers (384 dims)
- Upload to Qdrant vector database

Expected output:
```
🚀 Starting book content ingestion (FREE VERSION)...
📦 Using Sentence Transformers for embeddings (384 dimensions)
Found 50 markdown files
Processing: ros2-architecture.md
  ✅ Uploaded 12 chunks
...
🎉 Ingestion complete!
📊 Total chunks uploaded: 450
```

⏱️ **Note**: First run downloads the model (~80MB). Takes ~5-10 minutes depending on book size.

### 5. Run Development Server

```bash
python main.py
```

or

```bash
uvicorn main:app --reload --port 8000
```

Server will run at: http://localhost:8000

### 6. Test API

Health check:
```bash
curl http://localhost:8000/health
```

Test chat:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is ROS 2?"}'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` or `/health` | GET | Health check |
| `/api/chat` | POST | Normal chat |
| `/api/chat-selection` | POST | Chat with selected text |
| `/api/feedback` | POST | Submit feedback |
| `/api/history/{session_id}` | GET | Get chat history |

## Deployment

### Railway (Recommended)

1. Create Railway account
2. New Project → Deploy from GitHub
3. Add environment variables
4. Deploy!

### Vercel

```bash
pip install vercel
vercel --prod
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Cost Estimation

### FREE Version (Current):
- **Google Gemini**: $0 (FREE tier - 1500 requests/day)
- **Sentence Transformers**: $0 (runs locally)
- **Neon Postgres**: $0 (FREE 3GB tier)
- **Qdrant Cloud**: $0 (FREE 1GB tier)
- **Railway/Vercel**: $0 (FREE hobby tier)

**Total: $0/month** 🎉

### OpenAI Version (Alternative):
- **Neon Postgres**: Free (3GB)
- **Qdrant Cloud**: Free (1GB)
- **OpenAI API**: ~$5-10/month
  - Embeddings: $0.0001 per 1K tokens (~$0.50 for entire book)
  - GPT-4o-mini: $0.15 per 1M input tokens

## Troubleshooting

**Database connection error**:
```
Check DATABASE_URL format and SSL mode
```

**Qdrant connection error**:
```
Verify QDRANT_URL and QDRANT_API_KEY
```

**OpenAI rate limit**:
```
Add delays or upgrade to higher tier
```

## License

MIT
