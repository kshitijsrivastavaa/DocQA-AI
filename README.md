# 🧠 DocQA — AI-Powered Document & Multimedia Q&A

[![CI/CD](https://github.com/yourusername/docqa/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/docqa/actions)
[![Coverage](https://codecov.io/gh/yourusername/docqa/badge.svg)](https://codecov.io/gh/yourusername/docqa)

A full-stack web application that lets you upload PDFs, audio, and video files — then chat with an AI that understands every word, extracts timestamps, and lets you jump to relevant moments.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📄 PDF Q&A | Extract and semantically search document content |
| 🎵 Audio Q&A | Transcribe with Whisper + ask questions |
| 🎬 Video Q&A | Transcribe + timestamp extraction + playback |
| 🔍 Semantic Search | FAISS vector similarity search |
| 💬 Streaming Chat | Real-time streaming responses via SSE |
| ⏱ Timestamp Jump | Click any timestamp to seek in the media player |
| 📝 Auto Summary | Auto-generated content summaries |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                     Docker Compose                      │
│                                                        │
│   ┌──────────────┐    ┌─────────────────────────────┐ │
│   │   Frontend   │    │         Backend              │ │
│   │   React +    │───▶│  FastAPI + LangChain         │ │
│   │   Vite       │    │  + OpenAI + Whisper          │ │
│   │   Port: 3000 │    │  Port: 8000                  │ │
│   └──────────────┘    └──────────────┬──────────────┘ │
│                                      │                  │
│              ┌───────────────────────┤                  │
│              ▼                       ▼                  │
│   ┌────────────────┐    ┌─────────────────────────┐   │
│   │  PostgreSQL    │    │  FAISS Index            │   │
│   │  (Metadata +   │    │  (Vector Embeddings)    │   │
│   │   Chat History)│    │  text-embedding-3-small  │   │
│   └────────────────┘    └─────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### Tech Stack

**Backend:** Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL, OpenAI API, Whisper (local), FAISS, pdfplumber  
**Frontend:** React 18, Vite, TanStack Query, React Router  
**DevOps:** Docker, Docker Compose, GitHub Actions CI/CD

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 1. Clone & Configure

```bash
git clone https://github.com/yourusername/docqa.git
cd docqa

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

### 3. Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL separately or use Docker:
docker run -d --name pg -e POSTGRES_DB=docqa -e POSTGRES_USER=docqa \
  -e POSTGRES_PASSWORD=docqa_pass -p 5432:5432 postgres:16-alpine

# Create .env in backend/
echo "DATABASE_URL=postgresql+asyncpg://docqa:docqa_pass@localhost:5432/docqa" > .env
echo "OPENAI_API_KEY=your-key-here" >> .env

uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:3000
```

---

## 📡 API Documentation

Full Swagger UI: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

### Core Endpoints

#### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/upload` | Upload a PDF/audio/video file |
| `GET` | `/api/documents/` | List all documents |
| `GET` | `/api/documents/{id}` | Get document details + summary |
| `DELETE` | `/api/documents/{id}` | Delete a document |

#### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/sessions` | Create a chat session for a document |
| `GET` | `/api/chat/sessions/{id}/messages` | Get chat history |
| `POST` | `/api/chat/sessions/{id}/stream` | Stream a chat response (SSE) |

#### Media
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/media/{id}/stream` | Stream audio/video with range request support |
| `GET` | `/api/media/{id}/segments` | Get transcription segments with timestamps |

### Example: Upload a PDF

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/document.pdf"
```

Response:
```json
{
  "id": "uuid",
  "original_filename": "document.pdf",
  "file_type": "pdf",
  "status": "pending",
  "created_at": "2024-01-01T00:00:00"
}
```

### Example: Streaming Chat

```bash
curl -X POST http://localhost:8000/api/chat/sessions/{session_id}/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the main conclusions?"}' \
  --no-buffer
```

---

## 🧪 Testing

### Backend (pytest)

```bash
cd backend
pytest --cov=app --cov-report=term-missing --cov-fail-under=95 -v
```

Coverage target: **95%+**

### Frontend (Vitest)

```bash
cd frontend
npm test
```

---

## 🐳 Docker

### Build individual images

```bash
# Backend
docker build -t docqa-backend ./backend

# Frontend
docker build -t docqa-frontend ./frontend
```

### Run full stack
```bash
docker compose up --build -d
docker compose logs -f
docker compose down
```

---

## 📁 Project Structure

```
docqa/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers
│   │   │   ├── documents.py
│   │   │   ├── chat.py
│   │   │   └── media.py
│   │   ├── core/           # Config, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic
│   │   │   ├── document_service.py  # PDF/Whisper/FAISS
│   │   │   └── chat_service.py      # OpenAI chat + streaming
│   │   └── tests/          # Test suite (95%+ coverage)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── components/     # Layout, shared components
│   │   ├── pages/          # Home (upload), DocumentView (chat)
│   │   └── services/       # API client
│   ├── package.json
│   └── Dockerfile
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions CI/CD
├── docker-compose.yml
└── README.md
```

---

## 💡 Design Decisions

- **Local Whisper** instead of Whisper API → Free transcription, no per-minute costs
- **FAISS** instead of Pinecone → Free vector search, runs in-process
- **PostgreSQL + SQLAlchemy async** → Production-grade, handles concurrent requests
- **SSE streaming** → Real-time chat feel without WebSocket complexity
- **Background tasks** → FastAPI BackgroundTasks for non-blocking file processing

---

## 🎯 Bonus Features Implemented

- ✅ FAISS vector search (semantic similarity)
- ✅ Real-time streaming responses (SSE)
- ✅ Timestamp extraction for audio/video
- ✅ One-click timestamp playback
- ✅ Docker Compose multi-container
- ✅ GitHub Actions CI/CD with 95%+ coverage gate

---

## 📝 License

MIT
