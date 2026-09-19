"""
Celery task definitions.
Wraps the async ocr_worker into a Celery task that can be executed
by a worker process with its own event loop.
"""
import asyncio
import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.tasks.process_prescription_task",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    acks_late=True,
)
def process_prescription_task(
    self,
    prescription_id: str,
    image_path: str,
    lang_hint: str = "en",
    is_handwritten: bool = True,
):
    """Celery task that dispatches the async OCR pipeline on a background worker."""
    from app.workers.ocr_worker import process_prescription_job

    try:
        asyncio.run(
            process_prescription_job(
                prescription_id=prescription_id,
                image_path=image_path,
                lang_hint=lang_hint,
                is_handwritten=is_handwritten,
            )
        )
    except Exception as exc:
        logger.exception(f"Prescription task failed for {prescription_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.tasks.generate_embedding_task",
    bind=True,
    max_retries=2,
    default_retry_delay=3,
)
def generate_embedding_task(self, message_id: str, text: str):
    """Generates and persists a pgvector embedding for a ChatMessage."""
    from app.workers.embedding_worker import persist_message_embedding
    try:
        asyncio.run(persist_message_embedding(message_id=message_id, text=text))
    except Exception as exc:
        logger.exception(f"Embedding task failed for message {message_id}: {exc}")
        raise self.retry(exc=exc)
