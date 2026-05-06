from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import mimetypes

from app.core.database import get_db
from app.models.document import Document

router = APIRouter()

MIME_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "m4a": "audio/mp4",
    "ogg": "audio/ogg",
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "avi": "video/x-msvideo",
    "webm": "video/webm",
    "mkv": "video/x-matroska",
}


@router.get("/{doc_id}/stream")
async def stream_media(doc_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Stream audio/video file with range request support."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    ext = doc.filename.rsplit(".", 1)[-1].lower()
    mime_type = MIME_TYPES.get(ext, "application/octet-stream")
    
    file_size = os.path.getsize(doc.file_path)
    range_header = request.headers.get("range")
    
    if range_header:
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0])
        end = int(range_match[1]) if range_match[1] else file_size - 1
        chunk_size = end - start + 1
        
        def iter_file():
            with open(doc.file_path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    data = f.read(min(65536, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
        
        return StreamingResponse(
            iter_file(),
            status_code=206,
            media_type=mime_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
            }
        )
    
    return FileResponse(doc.file_path, media_type=mime_type)


@router.get("/{doc_id}/segments")
async def get_segments(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Get transcription segments for a document."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "segments": doc.transcription_segments or [],
        "duration_seconds": doc.duration_seconds
    }
