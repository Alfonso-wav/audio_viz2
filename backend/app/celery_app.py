"""
Celery application configuration.
"""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "audio_viz",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (Spleeter memory leak mitigation)
)

celery_app.autodiscover_tasks(["app.worker"])
