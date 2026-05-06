import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.document import Document, ProcessingStatus
from app.models.chat_session import ChatSession
from app.services.chat_service import chat_stream, get_session_messages

router = APIRouter()


class CreateSessionRequest(BaseModel):
    document_id: str


class ChatRequest(BaseModel):
    message: str


@router.post("/sessions")
async def create_session(req: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == req.document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Document is not ready (status: {doc.status.value})")
    
    session = ChatSession(document_id=req.document_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return {"session_id": str(session.id), "document_id": str(doc.id)}


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    messages = await get_session_messages(session_id, db)
    return {"messages": messages}


@router.post("/sessions/{session_id}/stream")
async def stream_chat(session_id: str, req: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def generate():
        async for chunk in chat_stream(session_id, req.message, db):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
