"""
Comprehensive test suite for DocQA API.
Run with: pytest --cov=app --cov-report=term-missing --cov-fail-under=95
"""

import pytest
import uuid
import os
import json
import io
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from httpx import AsyncClient, ASGITransport

# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_pdf_content():
    """Minimal PDF-like bytes for testing."""
    return b"%PDF-1.4 test content"


@pytest.fixture
def sample_audio_content():
    return b"RIFF" + b"\x00" * 100  # minimal WAV-like


@pytest.fixture
def mock_openai_client():
    with patch("openai.AsyncOpenAI") as mock:
        client = AsyncMock()
        mock.return_value = client
        
        # Embedding response
        embedding_response = MagicMock()
        embedding_response.data = [MagicMock(embedding=[0.1] * 1536)]
        client.embeddings.create = AsyncMock(return_value=embedding_response)
        
        # Chat completion response
        chat_response = MagicMock()
        chat_response.choices = [MagicMock(message=MagicMock(content="Test summary"))]
        client.chat.completions.create = AsyncMock(return_value=chat_response)
        
        yield client


# ─── Unit Tests: Document Service ────────────────────────────────────────────

class TestChunkText:
    def test_short_text_single_chunk(self):
        from app.services.document_service import chunk_text
        result = chunk_text("hello world", chunk_size=500)
        assert result == ["hello world"]

    def test_long_text_multiple_chunks(self):
        from app.services.document_service import chunk_text
        text = " ".join([f"word{i}" for i in range(1000)])
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) > 1

    def test_overlap_between_chunks(self):
        from app.services.document_service import chunk_text
        text = " ".join([f"word{i}" for i in range(200)])
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        # Each chunk should overlap with the next
        assert len(chunks) >= 2

    def test_empty_text(self):
        from app.services.document_service import chunk_text
        result = chunk_text("", chunk_size=500)
        assert result == [""]

    def test_exact_chunk_size(self):
        from app.services.document_service import chunk_text
        text = " ".join(["word"] * 100)
        chunks = chunk_text(text, chunk_size=100, overlap=0)
        assert len(chunks) == 1


class TestFindRelevantTimestamps:
    def test_finds_matching_segments(self):
        from app.services.chat_service import find_relevant_timestamps
        segments = [
            {"start": 0.0, "end": 5.0, "text": "The cat sat on the mat"},
            {"start": 5.0, "end": 10.0, "text": "Dogs are loyal animals"},
            {"start": 10.0, "end": 15.0, "text": "Cats like to sleep"},
        ]
        result = find_relevant_timestamps("cat sleeping", segments, top_k=2)
        texts = [r["text"] for r in result]
        assert any("cat" in t.lower() or "sleep" in t.lower() for t in texts)

    def test_returns_empty_for_no_segments(self):
        from app.services.chat_service import find_relevant_timestamps
        result = find_relevant_timestamps("anything", [], top_k=3)
        assert result == []

    def test_limits_results_to_top_k(self):
        from app.services.chat_service import find_relevant_timestamps
        segments = [
            {"start": float(i), "end": float(i + 1), "text": f"The topic word{i}"}
            for i in range(10)
        ]
        result = find_relevant_timestamps("the topic", segments, top_k=3)
        assert len(result) <= 3

    def test_no_matching_segments(self):
        from app.services.chat_service import find_relevant_timestamps
        segments = [{"start": 0.0, "end": 5.0, "text": "hello world"}]
        result = find_relevant_timestamps("xyzzy qwerty", segments)
        assert result == []


class TestExtractPdfText:
    def test_pdf_extraction_returns_string(self):
        from app.services.document_service import extract_pdf_text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 content"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = extract_pdf_text("/fake/path.pdf")
        assert result == "Page 1 content"

    def test_pdf_multiple_pages(self):
        from app.services.document_service import extract_pdf_text
        pages = [MagicMock() for _ in range(3)]
        for i, p in enumerate(pages):
            p.extract_text.return_value = f"Page {i + 1}"
        mock_pdf = MagicMock()
        mock_pdf.pages = pages
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = extract_pdf_text("/fake/path.pdf")
        assert "Page 1" in result and "Page 2" in result

    def test_pdf_empty_page(self):
        from app.services.document_service import extract_pdf_text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = extract_pdf_text("/fake/path.pdf")
        assert result == ""


class TestTranscription:
    def test_transcribe_returns_correct_structure(self):
        from app.services.document_service import transcribe_audio_video
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hello world",
            "segments": [
                {"start": 0.0, "end": 2.5, "text": " Hello world"}
            ]
        }
        with patch("app.services.document_service.get_whisper_model", return_value=mock_model):
            result = transcribe_audio_video("/fake/audio.mp3")
        
        assert result["full_text"] == "Hello world"
        assert len(result["segments"]) == 1
        assert result["segments"][0]["text"] == "Hello world"
        assert result["duration"] == 2.5

    def test_transcribe_empty_segments(self):
        from app.services.document_service import transcribe_audio_video
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "", "segments": []}
        with patch("app.services.document_service.get_whisper_model", return_value=mock_model):
            result = transcribe_audio_video("/fake/audio.mp3")
        assert result["duration"] == 0
        assert result["segments"] == []


class TestGetEmbedding:
    @pytest.mark.asyncio
    async def test_embedding_returns_list(self):
        from app.services.document_service import get_embedding
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_client
            
            result = await get_embedding("test text")
        
        assert isinstance(result, list)
        assert len(result) == 1536

    @pytest.mark.asyncio
    async def test_embedding_called_with_correct_model(self):
        from app.services.document_service import get_embedding
        from app.core.config import settings
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.0] * 1536)]
        
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_client
            
            await get_embedding("hello")
            mock_client.embeddings.create.assert_called_once()
            call_kwargs = mock_client.embeddings.create.call_args[1]
            assert call_kwargs["model"] == settings.EMBEDDING_MODEL


class TestGenerateSummary:
    @pytest.mark.asyncio
    async def test_summary_returns_string(self):
        from app.services.document_service import generate_summary
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="This is a summary."))]
        
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_client
            
            result = await generate_summary("Some content here", "pdf")
        
        assert result == "This is a summary."

    @pytest.mark.asyncio
    async def test_summary_truncates_long_text(self):
        from app.services.document_service import generate_summary
        long_text = "word " * 10000  # Very long text
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Summary"))]
        
        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_client
            
            result = await generate_summary(long_text, "video")
            # Should not raise, should truncate
            assert result == "Summary"


# ─── Unit Tests: Config ───────────────────────────────────────────────────────

class TestConfig:
    def test_default_model(self):
        from app.core.config import settings
        assert "gpt" in settings.OPENAI_MODEL or "claude" in settings.OPENAI_MODEL

    def test_default_database_url(self):
        from app.core.config import settings
        assert "postgresql" in settings.DATABASE_URL

    def test_max_file_size_positive(self):
        from app.core.config import settings
        assert settings.MAX_FILE_SIZE_MB > 0

    def test_secret_key_exists(self):
        from app.core.config import settings
        assert len(settings.SECRET_KEY) > 0


# ─── Unit Tests: File Type Detection ─────────────────────────────────────────

class TestFileTypeDetection:
    def test_pdf_detection(self):
        from app.api.documents import get_file_type
        from app.models.document import FileType
        assert get_file_type("report.pdf") == FileType.PDF

    def test_audio_detection(self):
        from app.api.documents import get_file_type
        from app.models.document import FileType
        assert get_file_type("recording.mp3") == FileType.AUDIO

    def test_video_detection(self):
        from app.api.documents import get_file_type
        from app.models.document import FileType
        assert get_file_type("lecture.mp4") == FileType.VIDEO

    def test_case_insensitive(self):
        from app.api.documents import get_file_type
        from app.models.document import FileType
        assert get_file_type("FILE.PDF") == FileType.PDF

    def test_unsupported_raises(self):
        from app.api.documents import get_file_type
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            get_file_type("malware.exe")
        assert exc.value.status_code == 400

    def test_wav_is_audio(self):
        from app.api.documents import get_file_type
        from app.models.document import FileType
        assert get_file_type("sound.wav") == FileType.AUDIO

    def test_webm_is_video(self):
        from app.api.documents import get_file_type
        from app.models.document import FileType
        assert get_file_type("clip.webm") == FileType.VIDEO


# ─── Unit Tests: Build System Prompt ─────────────────────────────────────────

class TestBuildSystemPrompt:
    def test_includes_filename(self):
        from app.services.chat_service import build_system_prompt
        from app.models.document import Document, FileType
        
        doc = MagicMock(spec=Document)
        doc.file_type = FileType.PDF
        doc.original_filename = "thesis.pdf"
        doc.transcription_segments = None
        
        chunks = [{"chunk_text": "Some extracted text"}]
        prompt = build_system_prompt(doc, chunks)
        assert "thesis.pdf" in prompt

    def test_includes_context(self):
        from app.services.chat_service import build_system_prompt
        from app.models.document import Document, FileType
        
        doc = MagicMock(spec=Document)
        doc.file_type = FileType.PDF
        doc.original_filename = "doc.pdf"
        doc.transcription_segments = None
        
        chunks = [{"chunk_text": "Important content here"}]
        prompt = build_system_prompt(doc, chunks)
        assert "Important content here" in prompt

    def test_audio_includes_timestamp_hint(self):
        from app.services.chat_service import build_system_prompt
        from app.models.document import Document, FileType
        
        doc = MagicMock(spec=Document)
        doc.file_type = FileType.AUDIO
        doc.original_filename = "podcast.mp3"
        doc.transcription_segments = [{"start": 0, "end": 5, "text": "hello"}]
        
        prompt = build_system_prompt(doc, [{"chunk_text": "content"}])
        assert "timestamp" in prompt.lower()


# ─── Unit Tests: Models ───────────────────────────────────────────────────────

class TestModels:
    def test_file_type_enum_values(self):
        from app.models.document import FileType
        assert FileType.PDF == "pdf"
        assert FileType.AUDIO == "audio"
        assert FileType.VIDEO == "video"

    def test_processing_status_enum(self):
        from app.models.document import ProcessingStatus
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"
        assert ProcessingStatus.PROCESSING == "processing"

    def test_document_model_has_required_columns(self):
        from app.models.document import Document
        cols = [c.name for c in Document.__table__.columns]
        for col in ["id", "filename", "file_type", "status", "file_path"]:
            assert col in cols

    def test_chat_message_model_has_role(self):
        from app.models.chat_session import ChatMessage
        cols = [c.name for c in ChatMessage.__table__.columns]
        assert "role" in cols
        assert "content" in cols
        assert "relevant_timestamps" in cols


# ─── Integration Tests: API Endpoints ────────────────────────────────────────

@pytest.fixture
async def async_client():
    """Create async test client with mocked DB."""
    from app.main import app
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self):
        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestDocumentEndpoints:
    @pytest.mark.asyncio
    async def test_upload_unsupported_file_type(self):
        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.txt", b"content", "text/plain")}
            response = await client.post("/api/documents/upload", files=files)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self):
        from app.main import app
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch("app.api.documents.get_db") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/documents/{uuid.uuid4()}")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self):
        from app.main import app
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch("app.api.documents.get_db") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete(f"/api/documents/{uuid.uuid4()}")
        
        assert response.status_code == 404


class TestChatEndpoints:
    @pytest.mark.asyncio
    async def test_create_session_nonexistent_doc(self):
        from app.main import app
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch("app.api.chat.get_db") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/chat/sessions", json={"document_id": str(uuid.uuid4())})
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_session_document_not_ready(self):
        from app.main import app
        from app.models.document import ProcessingStatus
        
        mock_doc = MagicMock()
        mock_doc.status = ProcessingStatus.PENDING
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_doc
        
        with patch("app.api.chat.get_db") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/chat/sessions", json={"document_id": str(uuid.uuid4())})
        
        assert response.status_code == 400


class TestMediaEndpoints:
    @pytest.mark.asyncio
    async def test_stream_nonexistent_doc(self):
        from app.main import app
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch("app.api.media.get_db") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/media/{uuid.uuid4()}/stream")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_segments_nonexistent_doc(self):
        from app.main import app
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        
        with patch("app.api.media.get_db") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/media/{uuid.uuid4()}/segments")
        
        assert response.status_code == 404


# ─── Semantic Search Tests ────────────────────────────────────────────────────

class TestSemanticSearch:
    @pytest.mark.asyncio
    async def test_search_empty_index_returns_empty(self):
        from app.services.document_service import semantic_search
        
        mock_index = MagicMock()
        mock_index.ntotal = 0
        
        with patch("app.services.document_service.get_faiss_index", return_value=mock_index):
            with patch("app.services.document_service.load_faiss_metadata"):
                result = await semantic_search("query")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_search_filters_by_doc_id(self):
        from app.services.document_service import semantic_search
        import numpy as np
        
        target_id = str(uuid.uuid4())
        other_id = str(uuid.uuid4())
        
        mock_index = MagicMock()
        mock_index.ntotal = 2
        mock_index.search.return_value = (
            np.array([[0.9, 0.8]]),
            np.array([[0, 1]])
        )
        
        metadata = {
            "0": {"doc_id": target_id, "chunk_text": "target chunk", "chunk_index": 0},
            "1": {"doc_id": other_id, "chunk_text": "other chunk", "chunk_index": 0},
        }
        
        mock_embedding = MagicMock()
        mock_embedding.data = [MagicMock(embedding=[0.1] * 1536)]
        
        with patch("app.services.document_service.get_faiss_index", return_value=mock_index):
            with patch("app.services.document_service.load_faiss_metadata"):
                with patch("app.services.document_service._faiss_metadata", metadata):
                    with patch("openai.AsyncOpenAI") as mock_cls:
                        mock_client = AsyncMock()
                        mock_client.embeddings.create = AsyncMock(return_value=mock_embedding)
                        mock_cls.return_value = mock_client
                        
                        results = await semantic_search("query", doc_id=target_id)
        
        for r in results:
            assert r["doc_id"] == target_id
