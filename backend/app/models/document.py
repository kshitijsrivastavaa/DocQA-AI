from sqlalchemy import Column, String, Text, Float, Integer, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


class FileType(str, enum.Enum):
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    
    # Extracted content
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # For audio/video
    duration_seconds = Column(Float, nullable=True)
    transcription_segments = Column(JSON, nullable=True)  # [{start, end, text}]
    
    # Processing
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    error_message = Column(Text, nullable=True)
    
    # FAISS index reference
    faiss_index_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
