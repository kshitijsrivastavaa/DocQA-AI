import os
import uuid
import asyncio
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document, FileType, ProcessingStatus
from app.services.document_service import process_document

router = APIRouter()

ALLOWED_EXTENSIONS = {
    "pdf": FileType.PDF,
    "mp3": FileType.AUDIO,
    "wav": FileType.AUDIO,
    "m4a": FileType.AUDIO,
    "ogg": FileType.AUDIO,
    "mp4": FileType.VIDEO,
    "mov": FileType.VIDEO,
    "avi": FileType.VIDEO,
    "webm": FileType.VIDEO,
    "mkv": FileType.VIDEO,
}


def get_file_type(filename: str) -> FileType:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not supported")
    return ALLOWED_EXTENSIONS[ext]


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    summary: str | None
    duration_seconds: float | None
    created_at: str | None

    class Config:
        from_attributes = True


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_type = get_file_type(file.filename)
    
    # Check file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB")
    
    # Save file
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    ext = file.filename.rsplit(".", 1)[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = upload_dir / unique_filename
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create DB record
    doc = Document(
        filename=unique_filename,
        original_filename=file.filename,
        file_type=file_type,
        file_size=len(content),
        file_path=str(file_path),
        status=ProcessingStatus.PENDING
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    # Process in background
    doc_id = str(doc.id)
    background_tasks.add_task(run_processing, doc_id)
    
    return DocumentResponse(
        id=str(doc.id),
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_type=doc.file_type.value,
        file_size=doc.file_size,
        status=doc.status.value,
        summary=doc.summary,
        duration_seconds=doc.duration_seconds,
        created_at=doc.created_at.isoformat() if doc.created_at else None
    )


async def run_processing(doc_id: str):
    """Run document processing with its own DB session."""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await process_document(doc_id, db)


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return [
        DocumentResponse(
            id=str(d.id),
            filename=d.filename,
            original_filename=d.original_filename,
            file_type=d.file_type.value,
            file_size=d.file_size,
            status=d.status.value,
            summary=d.summary,
            duration_seconds=d.duration_seconds,
            created_at=d.created_at.isoformat() if d.created_at else None
        )
        for d in docs
    ]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=str(doc.id),
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_type=doc.file_type.value,
        file_size=doc.file_size,
        status=doc.status.value,
        summary=doc.summary,
        duration_seconds=doc.duration_seconds,
        created_at=doc.created_at.isoformat() if doc.created_at else None
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted"}
