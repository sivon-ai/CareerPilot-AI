from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)


class Settings(BaseModel):
    app_name: str = "CareerPilot AI"
    app_version: str = "0.1.0"
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="models/gemini-3.6-flash", alias="GEMINI_MODEL")
    embedding_model: str = Field(default="models/gemini-embedding-001", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=768, alias="EMBEDDING_DIMENSION")
    top_k: int = Field(default=5, alias="TOP_K")
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        alias="ALLOWED_ORIGINS",
    )
    max_file_size_mb: int = Field(default=10, alias="MAX_FILE_SIZE_MB")
    upload_dir: Path = Field(default=BASE_DIR / "data" / "uploads")
    processed_dir: Path = Field(default=BASE_DIR / "data" / "processed")
    metadata_dir: Path = Field(default=BASE_DIR / "data" / "metadata")
    vector_store_dir: Path = Field(default=BASE_DIR / "vector_store")

    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_key(cls, value: str) -> str:
        return value.strip()

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @classmethod
    def from_env(cls) -> "Settings":
        import os

        raw = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
            "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "models/gemini-3.6-flash"),
            "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001"),
            "EMBEDDING_DIMENSION": int(os.getenv("EMBEDDING_DIMENSION", "768")),
            "TOP_K": int(os.getenv("TOP_K", "5")),
            "CHUNK_SIZE": int(os.getenv("CHUNK_SIZE", "1000")),
            "CHUNK_OVERLAP": int(os.getenv("CHUNK_OVERLAP", "150")),
            "ALLOWED_ORIGINS": [
                origin.strip()
                for origin in os.getenv(
                    "ALLOWED_ORIGINS",
                    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
                ).split(",")
                if origin.strip()
            ],
            "MAX_FILE_SIZE_MB": int(os.getenv("MAX_FILE_SIZE_MB", "10")),
        }
        return cls(**raw)


settings = Settings.from_env()

for directory in [
    settings.upload_dir,
    settings.processed_dir,
    settings.metadata_dir,
    settings.vector_store_dir,
]:
    directory.mkdir(parents=True, exist_ok=True)

APP_NAME = settings.app_name
GEMINI_API_KEY = settings.gemini_api_key
GEMINI_MODEL = settings.gemini_model
EMBEDDING_MODEL = settings.embedding_model
EMBEDDING_DIMENSION = settings.embedding_dimension
TOP_K = settings.top_k
CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap
ALLOWED_ORIGINS = settings.allowed_origins
MAX_FILE_SIZE_BYTES = settings.max_file_size_bytes
UPLOAD_DIR = settings.upload_dir
VECTOR_STORE_DIR = settings.vector_store_dir
METADATA_DIR = settings.metadata_dir
DATA_DIR = BASE_DIR / "data"
