import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from groq import Groq

from app.core.config import settings
from app.models.document import Document, FileType
from app.models.chat_session import ChatSession, ChatMessage
from app.services.document_service import semantic_search

logger = logging.getLogger(__name__)


def find_relevant_timestamps(query: str, segments: list[dict], top_k: int = 3):
    if not segments:
        return []

    query_words = set(query.lower().split())
    scored = []

    for seg in segments:
        seg_words = set(seg["text"].lower().split())
        overlap = len(query_words & seg_words)
        if overlap > 0:
            scored.append({**seg, "relevance": overlap})

    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored[:top_k]


def build_system_prompt(doc: Document, context_chunks: list[dict]) -> str:
    context = "\n\n---\n\n".join([c["chunk_text"] for c in context_chunks])

    base = f"""You are an assistant helping users understand a {doc.file_type.value} file.

CONTENT:
{context}
"""

    if doc.file_type in (FileType.AUDIO, FileType.VIDEO) and doc.transcription_segments:
        base += "\nMention timestamps if relevant."

    return base


# ---------------- CHAT ---------------- #

async def chat_stream(
    session_id: str,
    user_message: str,
    db: AsyncSession
) -> AsyncGenerator[str, None]:

    # Get session
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        yield "Session not found."
        return

    # Get document
    result = await db.execute(select(Document).where(Document.id == session.document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        yield "Document not found."
        return

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=user_message
    )
    db.add(user_msg)
    await db.commit()

    # Context
    context_chunks = await semantic_search(user_message, doc_id=str(doc.id), top_k=5)

    timestamps = []
    if doc.file_type in (FileType.AUDIO, FileType.VIDEO) and doc.transcription_segments:
        timestamps = find_relevant_timestamps(user_message, doc.transcription_segments)

    # History
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .limit(10)
    )
    history = history_result.scalars().all()

    # Build messages
    messages = [{"role": "system", "content": build_system_prompt(doc, context_chunks)}]

    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_message})

    # 🔥 GROQ CALL (NO STREAM)
    client = Groq(api_key=settings.GROQ_API_KEY)

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages
    )

    full_response = response.choices[0].message.content

    # Simulate streaming (optional)
    for word in full_response.split():
        yield word + " "

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=full_response,
        relevant_timestamps=timestamps if timestamps else None
    )
    db.add(assistant_msg)
    await db.commit()


# ---------------- FETCH ---------------- #

async def get_session_messages(session_id: str, db: AsyncSession):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "relevant_timestamps": m.relevant_timestamps,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in messages
    ]
