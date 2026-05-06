
# ================= IMPORTS ================= #

import json
import logging
import traceback
import subprocess
import os
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

# ================= FAISS ================= #

def get_faiss_index():
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


# ================= TEXT ================= #

def chunk_text(text: str, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    i = 0

    while i < len(words):
        chunks.append(" ".join(words[i:i+chunk_size]))
        i += chunk_size - overlap

    return chunks


async def get_embedding(text: str):
    return [0.0] * 384


async def index_document(doc_id: str, text: str):
    load_faiss_metadata()
    index = get_faiss_index()

    chunks = chunk_text(text)
    vectors = []

    for i, chunk in enumerate(chunks):
        vec = np.array(await get_embedding(chunk), dtype=np.float32)
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


# ================= SEARCH ================= #

async def semantic_search(query: str, doc_id=None, top_k=5):
    load_faiss_metadata()
    index = get_faiss_index()

    if index.ntotal == 0:
        return []

    q = np.array(await get_embedding(query), dtype=np.float32).reshape(1, -1)
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


# ================= PDF ================= #

def extract_pdf_text(file_path: str):
    text_parts = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)

    return "\n\n".join(text_parts)


# ================= AUDIO / VIDEO ================= #

def _make_segments(text: str):
    words = text.split()
    segments = []
    chunk = 20

    for i in range(0, len(words), chunk):
        segments.append({
            "start": i,
            "end": i + chunk,
            "text": " ".join(words[i:i+chunk])
        })

    return segments


async def transcribe_audio_video(file_path: str):
    client = Groq(api_key=settings.GROQ_API_KEY)

    if not file_path.lower().endswith((".mp3", ".wav")):
        audio_path = file_path + ".mp3"

        subprocess.run(
            ["ffmpeg", "-i", file_path, "-vn", "-acodec", "mp3", "-y", audio_path],
            check=True
        )
    else:
        audio_path = file_path

    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=f,
            model=settings.GROQ_WHISPER_MODEL
        )

    if audio_path != file_path:
        try:
            os.remove(audio_path)
        except:
            pass

    return {
        "full_text": transcription.text,
        "segments": _make_segments(transcription.text)
    }


# ================= SUMMARY ================= #

async def generate_summary(text: str, file_type: str):
    client = Groq(api_key=settings.GROQ_API_KEY)

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{
            "role": "user",
            "content": f"Summarize this {file_type} content:\n\n{text[:4000]}"
        }]
    )

    return response.choices[0].message.content


# ================= MAIN ================= #

async def process_document(doc_id: str, db: AsyncSession):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()

    if not doc:
        return

    try:
        doc.status = ProcessingStatus.PROCESSING
        await db.commit()

        if doc.file_type == FileType.PDF:
            text = extract_pdf_text(doc.file_path)

        elif doc.file_type in (FileType.AUDIO, FileType.VIDEO):
            transcription = await transcribe_audio_video(doc.file_path)

            text = transcription["full_text"]
            doc.transcription_segments = transcription["segments"]

        else:
            text = ""

        if not text.strip():
            raise ValueError("No text extracted")

        summary = await generate_summary(text, doc.file_type.value)

        await index_document(str(doc.id), text)

        doc.extracted_text = text
        doc.summary = summary
        doc.status = ProcessingStatus.COMPLETED

        await db.commit()

    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()

        doc.status = ProcessingStatus.FAILED
        doc.error_message = str(e)

        await db.commit()

