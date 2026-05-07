# 🧠 DocQA — AI-Powered Document & Multimedia Q&A
<div align="center">

<p align="center">
  <a href="https://docqa-ai.vercel.app">
    <img src="https://img.shields.io/badge/Live-Demo-blue?style=for-the-badge&logo=vercel" />
  </a>
  <a href="https://docqa-ai-production.up.railway.app/health">
    <img src="https://img.shields.io/badge/Backend-API-green?style=for-the-badge&logo=fastapi" />
  </a>
  <a href="https://docqa-ai-production.up.railway.app/docs">
    <img src="https://img.shields.io/badge/Swagger-Docs-orange?style=for-the-badge&logo=swagger" />
  </a>
  <a href="https://github.com/kshitijsrivastavaa/DocQA-AI">
    <img src="https://img.shields.io/github/stars/kshitijsrivastavaa/DocQA-AI?style=for-the-badge" />
  </a>
</p>

</div>

---

## 🎬 Demo 

<div align="center">
  <a href="https://github.com/kshitijsrivastavaa/DocQA-AI/issues/1#issue-4401186302">
    🎬 Watch Demo Video
  </a>
</div>

## 📸 Screenshots

<!-- ============================================================
     HOW TO ADD SCREENSHOTS:
     1. Create a folder called "assets" inside your repo
     2. Take screenshots of each feature below
     3. Name them as shown and upload to the assets folder
     4. The images will auto-appear here!
     ============================================================ -->

### 🏠 Home — Upload Screen
<div align="center">
  <img src="https://raw.githubusercontent.com/kshitijsrivastavaa/DocQA-AI/refs/heads/main/pictures/Landing_Page.png" alt="Home Screen" width="800"/>
</div>

---

### 💬 AI Chat Interface
<div align="center">
  <img src="https://raw.githubusercontent.com/kshitijsrivastavaa/DocQA-AI/main/pictures/Chat_Interaction.png" alt="Chat Interface" width="800"/>
</div>

---

### 🎬 Video Q&A with Timestamps
<div align="center">
  <img src="https://raw.githubusercontent.com/kshitijsrivastavaa/DocQA-AI/refs/heads/main/pictures/Timestamp.png" alt="Video Q&A" width="800"/>
</div>

---

### 🎧 Features
<div align="center">
  <img src="https://raw.githubusercontent.com/kshitijsrivastavaa/DocQA-AI/refs/heads/main/pictures/Features.png" alt="Audio Transcription" width="800"/>
</div>

---

## 🚀 About

🧠 **DocQA** is a full-stack AI-powered application that allows users to upload **PDFs, audio, and video files** and interact with them using natural language queries.

💡 Instead of manually reading or watching content, users can simply **ask questions and get instant AI-generated answers.**

---

## ✨ Key Highlights

- 📄 **PDF Understanding** — Extract and query document content
- 🎧 **Audio/Video Transcription** — Powered by Groq Whisper
- 💬 **AI Chat Interface** — Ask anything about your content
- 🔍 **Semantic Search (FAISS)** — Smart retrieval of relevant chunks
- ⚡ **Real-time Streaming Responses**
- 🧠 **Automatic Summarization**
- ⏱️ **Timestamp Jump** — Click timestamps to seek in media player
- 🐳 **Fully Dockerized** with GitHub Actions CI/CD

---

## 🔥 Live Links

- 🌐 **Frontend:** https://docqa-ai.vercel.app
- ⚙️ **Backend API:** https://docqa-ai-production.up.railway.app
- 📚 **API Docs:** https://docqa-ai-production.up.railway.app/docs

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 (Vite), TanStack Query, React Router |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy (async) |
| **AI / ML** | Groq LLM, Groq Whisper, LangChain, FAISS |
| **Database** | PostgreSQL |
| **DevOps** | Docker, Docker Compose, GitHub Actions CI/CD |
| **Deployment** | Vercel (Frontend) + Railway (Backend) |

---

## ✨ Features

| Feature | Details |
|---------|---------|
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
│   │   Vite       │    │  + Groq + Whisper            │ │
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

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 1. Clone & Configure

```bash
git clone https://github.com/kshitijsrivastavaa/DocQA-AI.git
cd DocQA-AI
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

### 3. Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Endpoints

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/upload` | Upload PDF/audio/video |
| `GET` | `/api/documents/` | List all documents |
| `GET` | `/api/documents/{id}` | Get document + summary |
| `DELETE` | `/api/documents/{id}` | Delete a document |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/sessions` | Create chat session |
| `GET` | `/api/chat/sessions/{id}/messages` | Get chat history |
| `POST` | `/api/chat/sessions/{id}/stream` | Stream chat (SSE) |

### Media
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/media/{id}/stream` | Stream audio/video |
| `GET` | `/api/media/{id}/segments` | Get transcript + timestamps |

---

## 🧪 Testing

```bash
cd backend
pytest --cov=app --cov-report=term-missing --cov-fail-under=95 -v
```

Coverage target: **95%+** ✅

---

## 💡 Design Decisions

- **Local Whisper** instead of Whisper API → Free transcription, no per-minute costs
- **FAISS** instead of Pinecone → Free vector search, runs in-process
- **PostgreSQL + SQLAlchemy async** → Production-grade, handles concurrent requests
- **SSE streaming** → Real-time chat feel without WebSocket complexity
- **Background tasks** → FastAPI BackgroundTasks for non-blocking file processing

---

## 🎯 Bonus Features

- ✅ FAISS vector search (semantic similarity)
- ✅ Real-time streaming responses (SSE)
- ✅ Timestamp extraction for audio/video
- ✅ One-click timestamp playback
- ✅ Docker Compose multi-container
- ✅ GitHub Actions CI/CD with 95%+ coverage gate

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
## 👨‍💻 Author

<div align="center">

### Kshitij Srivastava

📧 Email: <a href="mailto:kshitij.srivastava16@gmail.com">kshitij.srivastava16@gmail.com</a>

💻 GitHub: <a href="https://github.com/kshitijsrivastavaa">kshitijsrivastavaa</a>

</div>

## 📝 License

MIT

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:7aa2f7,50:414868,100:1a1b27&height=100&section=footer"/>
</div>
