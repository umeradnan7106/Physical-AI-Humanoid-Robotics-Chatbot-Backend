# Railway Deployment Setup

## Quick Deploy to Railway

### Step 1: Create New Railway Project
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose: **Physical-AI-Humanoid-Robotics-Chatbot-Backend**

### Step 2: Add Environment Variables

In Railway Settings → Variables, add these 5 variables:

| Variable Name | Description | Example |
|--------------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API Key | Get from https://makersuite.google.com/app/apikey |
| `QDRANT_URL` | Qdrant Cloud URL | https://xxx.qdrant.io |
| `QDRANT_API_KEY` | Qdrant API Key | Your Qdrant API key |
| `QDRANT_COLLECTION_NAME` | Collection name | physical_ai_book |
| `DATABASE_URL` | Neon Postgres URL | postgresql://user:pass@host.neon.tech/db?sslmode=require |

### Step 3: Deploy

Railway will automatically:
- ✅ Detect Python from `requirements.txt`
- ✅ Install all dependencies (FastAPI, Google Gemini, etc.)
- ✅ Start the server using `Procfile`
- ✅ Assign a public URL

### Step 4: Test Deployment

Once deployed, test these endpoints:

1. **Health Check:**
   ```
   https://your-app.up.railway.app/health
   ```
   Response: `{"status":"healthy"...}`

2. **API Documentation:**
   ```
   https://your-app.up.railway.app/docs
   ```
   Interactive API docs with all endpoints

3. **Chat Endpoint:**
   ```bash
   curl -X POST https://your-app.up.railway.app/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What is physical AI?"}'
   ```

### Step 5: Get Your Railway URL

After successful deployment:
1. Go to Railway Settings → Domains
2. Copy your URL (e.g., `https://physical-ai-chatbot-production-xxxx.up.railway.app`)
3. Use this URL in your frontend chatbot configuration

---

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/chat` | POST | Chat with RAG AI |
| `/feedback` | POST | Submit feedback |
| `/analytics` | GET | Get analytics |
| `/docs` | GET | API documentation |

---

## FREE Services Used

- **AI Model:** Google Gemini 2.5 Flash (1500 requests/day)
- **Embeddings:** Sentence Transformers (local, unlimited)
- **Vector DB:** Qdrant Cloud (1GB free)
- **Database:** Neon Postgres (3GB free)
- **Deployment:** Railway (free tier)

**Total Cost: $0/month** ✅

---

## Troubleshooting

### Build Fails
- Check that all files are committed
- Verify `requirements.txt` is present
- Check Railway build logs for errors

### Runtime Crashes
- Verify all 5 environment variables are set
- Check Railway deployment logs
- Ensure DATABASE_URL and QDRANT_URL are valid

### 502 Bad Gateway
- App crashed at startup
- Check Railway logs for error messages
- Verify environment variables are correct

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with variables
cp .env.example .env
# Edit .env and add your API keys

# Run server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Server runs at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

---

## Next Steps After Deployment

1. ✅ Copy Railway URL
2. ✅ Update frontend chatbot with Railway URL
3. ✅ Deploy frontend to GitHub Pages
4. ✅ Test live chatbot

---

**Repository:** https://github.com/umeradnan7106/Physical-AI-Humanoid-Robotics-Chatbot-Backend
**Frontend Repo:** https://github.com/umeradnan7106/Physical-AI-Humanoid-Robotics-Course
