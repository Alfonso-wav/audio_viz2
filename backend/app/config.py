"""
Configuration settings for the Audio Visualizer backend.
Uses environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    # Storage
    temp_dir: Path = Path("/tmp/audio_viz")
    max_audio_duration: int = 60  # seconds
    job_ttl: int = 3600  # 1 hour TTL for temp files

    # Video export
    video_width: int = 1280
    video_height: int = 720
    video_fps: int = 30

    # Limits
    max_upload_size_mb: int = 10  # per image
    max_concurrent_jobs: int = 4

    class Config:
        env_prefix = "AUDIOVIZ_"


settings = Settings()

# Ensure temp dir exists
settings.temp_dir.mkdir(parents=True, exist_ok=True)
