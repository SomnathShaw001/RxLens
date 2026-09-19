from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.database import engine, Base
from app.core.exceptions import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
)
from app.api.v1.api import api_router
from app.services.storage import StorageService
import app.models  # Ensure all models are imported before create_all
import logging

logger = logging.getLogger(__name__)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables and ensure upload directory exists."""
    StorageService.ensure_local_dir()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("RxLens API started — tables ensured, storage ready.")
    yield
    await engine.dispose()
    logger.info("RxLens API shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "**RxLens API** — Multilingual AI Prescription Digitization Platform.\n\n"
        "Provides prescription OCR ingestion, confidence-gated extraction, "
        "drug intelligence, medication tracking, and AI chat."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─── Middleware ────────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production via env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Error Handlers ───────────────────────────────────────────────────────────
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ─── API Routers ──────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


# ─── Health & Root ────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint used by Render keep-alive and uptime monitors."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Welcome to RxLens Backend API",
        "docs": "/docs",
        "health": "/health",
        "version": settings.VERSION,
    }
