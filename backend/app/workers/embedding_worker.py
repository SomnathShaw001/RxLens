"""Persists pgvector embeddings for chat messages."""
import logging
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.chat import ChatMessage
from app.services.embeddings import get_text_embedding

logger = logging.getLogger(__name__)


async def persist_message_embedding(message_id: str, text: str):
    """Generates and saves the embedding vector for a ChatMessage row."""
    embedding = await get_text_embedding(text)
    if embedding is None:
        logger.warning(f"Skipping embedding persistence for {message_id} (API not configured).")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )
        message = result.scalar_one_or_none()
        if message:
            message.embedding = embedding
            await session.commit()
            logger.info(f"Embedding saved for message {message_id}.")
