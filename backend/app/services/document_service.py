import json
import logging
import traceback
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
import pdfplumber
from groq import Groq
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.document import Document, ProcessingStatus, FileType

logger = logging.getLogger(__name__)

_faiss_index: Optional[faiss.Index] = None
_faiss_metadata: dict = {}

# ---------------- FAISS ---------------- #

def get_faiss_index() -> faiss.Index:
    global _faiss_index
    if _faiss_index is None:
        index_path = Path(settings.FAISS_INDEX_PATH) / "index.faiss"
        if index_path.exists():
            _faiss_index = faiss.read_index(str(index_path))
        else:
            _faiss_index = faiss.IndexFlatIP(384)
    return _faiss_index


def save_faiss_index():
    index_path = Path(settings.FAISS_INDEX_PATH)
    index_path.mkdir(parents=True, exist_ok=True)

    faiss.write_index(get_faiss_index(), str(index_path / "index.faiss"))

    with open(index_path / "metadata.json", "w") as f:
        json.dump(_faiss_metadata, f)


def load_faiss_metadata():
    global _faiss_metadata
    meta_path = Path(settings.FAISS_INDEX_PATH) / "metadata.json"
    if meta_path.exists():
        with open(meta_path) as f:
            _faiss_metadata = json.load(f)


# ---------------- TEXT ---------------- #

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50):
    words = text.split()
    chunks = []
    i = 0

    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap

    return chunks


# 🔥 Lightweight dummy embedding (NO heavy deps)
async def get_embedding(text: str):
    return [0.0] * 384


async def index_document(doc_id: str, text: str):
    load_faiss_metadata()
    index = get_faiss_index()

    chunks = chunk_text(text)
    vectors = []

    for i, chunk in enumerate(chunks):
        emb = await get_embedding(chunk)
        vec = np.array(emb, dtype=np.float32)
        faiss.normalize_L2(vec.reshape(1, -1))
        vectors.append(vec)

        _faiss_metadata[str(index.ntotal + len(vectors) - 1)] = {
            "doc_id": doc_id,
            "chunk_text": chunk,
            "chunk_index": i
        }

    if vectors:
        index.add(np.vstack(vectors))

    save_faiss_index()


# ---------------- SEARCH ---------------- #

async def semantic_search(query: str, doc_id: Optional[str] = None, top_k: int = 5):
    load_faiss_metadata()
    index = get_faiss_index()

    if index.ntotal == 0:
        return []

    query_vec = await get_embedding(query)
    q = np.array(query_vec, dtype=np.float32).reshape(1, -1)
    faiss.normalize_L2(q)

    scores, ids = index.search(q, min(top_k, index.ntotal))

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue

        meta = _faiss_metadata.get(str(idx))
        if not meta:
            continue

        if doc_id and meta["doc_id"] != doc_id:
            continue

        results.append({
            "chunk_text": meta["chunk_text"],
            "score": float(score)
        })

    return results


# ---------------- PDF ---------------- #

def extract_pdf_text(file_path: str):
    text_parts = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n\n".join(text_parts)


# ---------------- AUDIO / VIDEO ---------------- #

import subprocess
import os
from groq import Groq
from app.core.config import settings


async def transcribe_audio_video(file_path: str):
    client = Groq(api_key=settings.GROQ_API_KEY)

    # If already audio → use directly
    if file_path.lower().endswith((".mp3", ".wav")):
        audio_path = file_path
    else:
        # Convert video → audio
        audio_path = file_path + ".mp3"

        try:
            subprocess.run([
                "ffmpeg",
                "-i", file_path,
                "-vn",              # remove video
                "-acodec", "mp3",
                "-y",
                audio_path
            ], check=True)
        except Exception as e:
            print("❌ ffmpeg conversion failed:", e)
            raise

    # Send to Groq
    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=f,
            model=settings.GROQ_WHISPER_MODEL
        )

    # Cleanup temp file
    if audio_path != file_path:
        try:
            os.remove(audio_path)
        except:
            pass

    def _make_segments(text: str):
    words = text.split()
    segments = []
    chunk_size = 20

    for i in range(0, len(words), chunk_size):
        segments.append({
            "start": i,
            "end": i + chunk_size,
            "text": " ".join(words[i:i+chunk_size])
        })

    return segments


text = transcription.text

return {
    "full_text": text,
    "segments": _make_segments(text)
}

# ---------------- SUMMARY ---------------- #

async def generate_summary(text: str, file_type: str):
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""
Summarize this {file_type} content clearly.

Include:
- key points
- important insights

Content:
{text[:4000]}
"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ---------------- MAIN PROCESS ---------------- #

async def process_document(doc_id: str, db: AsyncSession):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()

    if not doc:
        print("❌ Document not found")
        return

    try:
        doc.status = ProcessingStatus.PROCESSING
        await db.commit()

        # -------- extract ----------
        if doc.file_type == FileType.PDF:
            print("📄 Extracting PDF")
            text = extract_pdf_text(doc.file_path)

        elif doc.file_type in (FileType.AUDIO, FileType.VIDEO):
            print("🎧 Transcribing audio/video")
            text = await transcribe_audio_video(doc.file_path)

         text = transcription["full_text"]
         segments = transcription["segments"]
        doc.transcription_segments = segments

        if not text.strip():
            raise ValueError("No text extracted")

        print("✅ Text extracted")

        # -------- summary ----------
        summary = await generate_summary(text, doc.file_type.value)
        print("✅ Summary generated")

        # -------- indexing ----------
        await index_document(str(doc.id), text)

        doc.extracted_text = text
        doc.summary = summary
        doc.status = ProcessingStatus.COMPLETED

        await db.commit()

        print("🎉 DONE")

    except Exception as e:
        print("\n🔥 ERROR OCCURRED")
        print(e)
        traceback.print_exc()

        doc.status = ProcessingStatus.FAILED
        doc.error_message = str(e)
        await db.commit()
