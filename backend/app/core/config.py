from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "DocQA"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://docqa:docqa_pass@db:5432/docqa"

    # 🔥 GROQ CONFIG (only this matters now)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # Whisper (for audio/video)
    GROQ_WHISPER_MODEL: str = "whisper-large-v3"

    # Storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE_MB: int = 100
    FAISS_INDEX_PATH: str = "/app/faiss_index"

    # Optional
    REDIS_URL: Optional[str] = None

    # Auth
    SECRET_KEY: str = "change-me-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
