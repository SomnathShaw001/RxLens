"""Embedding service using Google Gemini text-embedding-004 for RAG retrieval."""
import logging
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from pgvector.sqlalchemy import Vector
    _pgvector_available = True
except ImportError:
    _pgvector_available = False

try:
    from google import genai
    _genai_available = True
except ImportError:
    _genai_available = False

EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSION = 768


async def get_text_embedding(text: str) -> Optional[List[float]]:
    """
    Generate a 768-dim embedding vector for the given text using Gemini embeddings.
    Returns None if API is unavailable (dev mode fallback).
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "your-gemini-api-key-here" or not _genai_available:
        logger.warning("Gemini API not configured — embedding skipped (dev mode).")
        return None

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None


async def get_batch_embeddings(texts: List[str]) -> List[Optional[List[float]]]:
    """Generates embeddings for a batch of texts."""
    results = []
    for text in texts:
        emb = await get_text_embedding(text)
        results.append(emb)
    return results
