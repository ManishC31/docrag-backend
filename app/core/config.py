from functools import lru_cache
from typing import Annotated, Any

from pydantic import AnyHttpUrl, BeforeValidator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str]:
    if isinstance(v, str):
        import json
        return json.loads(v)
    return v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # App
    APP_NAME: str = "RAG Application"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str
    SYNC_DATABASE_URL: str

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "document_chunks"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI
    OPENAI_API_KEY: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str | None = None

    # CORS
    BACKEND_CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors)] = []

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: Annotated[list[str], BeforeValidator(parse_cors)] = ["pdf", "txt", "docx"]

    # RAG
    MAX_DOCUMENTS_PER_GROUP: int = 3
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    CHAT_MODEL: str = "gpt-4o"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_CHUNKS: int = 5

    # Admin
    ADMIN_EMAIL: str = "manishchavan80@gmail.com"

    @computed_field
    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
