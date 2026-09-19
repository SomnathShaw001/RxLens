"""Celery application configured with Redis broker for asynchronous task queue."""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "rxlens",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,  # Results expire after 1 hour
    task_routes={
        "app.workers.tasks.process_prescription_task": {"queue": "ocr"},
        "app.workers.tasks.generate_embedding_task": {"queue": "embeddings"},
    },
)
