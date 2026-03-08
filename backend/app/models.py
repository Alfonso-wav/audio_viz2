"""
Job model and state management using Redis.
No persistent database — all data lives in Redis with TTL.
"""

from __future__ import annotations

import json
import uuid
import time
from enum import Enum
from typing import Optional
from pathlib import Path

import redis

from app.config import settings


class JobStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    SEPARATING = "separating"
    ANALYZING = "analyzing"
    WAITING_IMAGES = "waiting_images"
    RENDERING = "rendering"
    DONE = "done"
    ERROR = "error"


class Job:
    """Represents a visualization job stored in Redis."""

    def __init__(
        self,
        job_id: str,
        youtube_url: str,
        status: JobStatus = JobStatus.QUEUED,
        progress: float = 0.0,
        error: Optional[str] = None,
        created_at: Optional[float] = None,
        audio_duration: Optional[float] = None,
        stems_ready: bool = False,
        images_uploaded: int = 0,
        visual_spec: Optional[dict] = None,
    ):
        self.job_id = job_id
        self.youtube_url = youtube_url
        self.status = status
        self.progress = progress
        self.error = error
        self.created_at = created_at or time.time()
        self.audio_duration = audio_duration
        self.stems_ready = stems_ready
        self.images_uploaded = images_uploaded
        self.visual_spec = visual_spec

    @property
    def dir(self) -> Path:
        """Job working directory on disk."""
        return settings.temp_dir / self.job_id

    def to_dict(self) -> dict:
        d = {
            "job_id": self.job_id,
            "youtube_url": self.youtube_url,
            "status": self.status.value,
            "progress": float(self.progress),
            "created_at": float(self.created_at),
            "stems_ready": int(self.stems_ready),  # Redis rejects bool
            "images_uploaded": int(self.images_uploaded),
        }
        # Redis hset rejects None values — only include optional fields when set
        if self.error is not None:
            d["error"] = self.error
        if self.audio_duration is not None:
            d["audio_duration"] = self.audio_duration
        if self.visual_spec is not None:
            d["visual_spec"] = json.dumps(self.visual_spec)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Job:
        vs = data.get("visual_spec")
        if vs in (None, "None", ""):
            vs = None

        error = data.get("error")
        if error in ("None", ""):
            error = None

        return cls(
            job_id=data["job_id"],
            youtube_url=data["youtube_url"],
            status=JobStatus(data["status"]),
            progress=float(data.get("progress", 0)),
            error=error,
            created_at=float(data["created_at"]),
            audio_duration=float(data["audio_duration"]) if data.get("audio_duration") not in (None, "None", "") else None,
            stems_ready=data.get("stems_ready") in (True, "True", "true", "1", 1),
            images_uploaded=int(data.get("images_uploaded", 0)),
            visual_spec=json.loads(vs) if vs else None,
        )


# ── Redis helpers ──────────────────────────────────────────────

_redis: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _key(job_id: str) -> str:
    return f"job:{job_id}"


def create_job(youtube_url: str) -> Job:
    job_id = uuid.uuid4().hex[:12]
    job = Job(job_id=job_id, youtube_url=youtube_url)
    job.dir.mkdir(parents=True, exist_ok=True)
    r = get_redis()
    r.hset(_key(job_id), mapping=job.to_dict())
    r.expire(_key(job_id), settings.job_ttl)
    return job


def get_job(job_id: str) -> Optional[Job]:
    r = get_redis()
    data = r.hgetall(_key(job_id))
    if not data:
        return None
    return Job.from_dict(data)


def update_job(job: Job, **fields) -> Job:
    for k, v in fields.items():
        setattr(job, k, v)
    r = get_redis()
    r.hset(_key(job.job_id), mapping=job.to_dict())
    r.expire(_key(job.job_id), settings.job_ttl)
    return job


def list_jobs() -> list[str]:
    r = get_redis()
    return [k.replace("job:", "") for k in r.keys("job:*")]
