from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import documents, chat, media
from app.core.database import init_db
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up DocQA API...")
    await init_db()
    yield
    logger.info("Shutting down DocQA API...")


app = FastAPI(
    title="DocQA - AI Document & Multimedia Q&A",
    description="Upload PDFs, audio, and video files and chat with an AI about their content.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(media.router, prefix="/api/media", tags=["Media"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
