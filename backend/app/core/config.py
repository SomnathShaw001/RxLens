import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "RxLens Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rxlens"
    SYNC_DATABASE_URL: Optional[str] = "postgresql://postgres:postgres@localhost:5432/rxlens"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./uploads"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_BUCKET: str = "prescriptions"

    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Firebase Auth
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None

    # JWT Authentication
    JWT_SECRET: str = "temporary-secret-key-change-in-production-rxlens-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Confidence Thresholds (TRD Section 10.3)
    CONFIDENCE_THRESHOLD_PRINTED: float = 85.0
    CONFIDENCE_THRESHOLD_HANDWRITTEN: float = 70.0


settings = Settings()
