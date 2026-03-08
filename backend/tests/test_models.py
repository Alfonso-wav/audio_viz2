"""
Tests for app.models — Job model CRUD and serialization.
"""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.models import Job, JobStatus


class TestJobModel:
    """Test Job class serialization and deserialization."""

    def test_job_creation_defaults(self):
        job = Job(job_id="abc123", youtube_url="https://youtube.com/watch?v=test")
        assert job.job_id == "abc123"
        assert job.youtube_url == "https://youtube.com/watch?v=test"
        assert job.status == JobStatus.QUEUED
        assert job.progress == 0.0
        assert job.error is None
        assert job.stems_ready is False
        assert job.images_uploaded == 0
        assert job.visual_spec is None
        assert job.created_at > 0

    def test_job_to_dict(self):
        job = Job(
            job_id="abc123",
            youtube_url="https://youtube.com/watch?v=test",
            status=JobStatus.DOWNLOADING,
            progress=0.5,
            created_at=1000.0,
        )
        d = job.to_dict()
        assert d["job_id"] == "abc123"
        assert d["status"] == "downloading"
        assert d["progress"] == 0.5
        assert d["created_at"] == 1000.0
        assert "visual_spec" not in d  # None fields omitted for Redis compatibility

    def test_job_to_dict_with_visual_spec(self):
        spec = {"fps": 30, "width": 1280}
        job = Job(
            job_id="abc123",
            youtube_url="https://youtube.com/watch?v=test",
            visual_spec=spec,
            created_at=1000.0,
        )
        d = job.to_dict()
        assert d["visual_spec"] == json.dumps(spec)

    def test_job_from_dict(self):
        data = {
            "job_id": "abc123",
            "youtube_url": "https://youtube.com/watch?v=test",
            "status": "separating",
            "progress": "0.6",
            "error": None,
            "created_at": "1000.0",
            "audio_duration": "10.5",
            "stems_ready": "True",
            "images_uploaded": "3",
            "visual_spec": None,
        }
        job = Job.from_dict(data)
        assert job.job_id == "abc123"
        assert job.status == JobStatus.SEPARATING
        assert job.progress == 0.6
        assert job.audio_duration == 10.5
        assert job.stems_ready is True
        assert job.images_uploaded == 3
        assert job.visual_spec is None

    def test_job_from_dict_with_visual_spec(self):
        spec = {"fps": 30, "layers": []}
        data = {
            "job_id": "abc123",
            "youtube_url": "https://youtube.com/watch?v=test",
            "status": "done",
            "progress": "1.0",
            "created_at": "1000.0",
            "visual_spec": json.dumps(spec),
        }
        job = Job.from_dict(data)
        assert job.visual_spec == spec

    def test_job_roundtrip(self):
        """to_dict → from_dict should preserve all fields."""
        original = Job(
            job_id="roundtrip",
            youtube_url="https://youtube.com/watch?v=x",
            status=JobStatus.RENDERING,
            progress=0.75,
            error="test error",
            created_at=1234567890.123,
            audio_duration=45.5,
            stems_ready=True,
            images_uploaded=5,
            visual_spec={"fps": 30, "width": 1280},
        )
        restored = Job.from_dict(original.to_dict())
        assert restored.job_id == original.job_id
        assert restored.status == original.status
        assert restored.progress == original.progress
        assert restored.error == original.error
        assert restored.audio_duration == original.audio_duration
        assert restored.stems_ready == original.stems_ready
        assert restored.images_uploaded == original.images_uploaded
        assert restored.visual_spec == original.visual_spec

    def test_job_dir(self, temp_dir):
        job = Job(job_id="dirtest", youtube_url="https://youtube.com/watch?v=x")
        assert job.dir == temp_dir / "dirtest"

    def test_to_dict_no_none_values(self):
        """Redis hset rejects None — to_dict must never contain None values."""
        job = Job(
            job_id="nonetest",
            youtube_url="https://youtube.com/watch?v=x",
            created_at=1000.0,
            # These default to None:
            error=None,
            audio_duration=None,
            visual_spec=None,
        )
        d = job.to_dict()
        for key, value in d.items():
            assert value is not None, f"to_dict()['{key}'] is None — Redis will reject this"

    def test_to_dict_redis_safe_types(self):
        """Redis hset only accepts bytes, str, int, float. No bool or other types."""
        job = Job(
            job_id="typetest",
            youtube_url="https://youtube.com/watch?v=x",
            created_at=1000.0,
            stems_ready=True,
            error="some error",
            audio_duration=30.0,
            visual_spec={"fps": 30},
        )
        d = job.to_dict()
        allowed = (str, int, float, bytes)
        for key, value in d.items():
            assert isinstance(value, allowed), (
                f"to_dict()['{key}'] is {type(value).__name__} — Redis only accepts str/int/float/bytes"
            )

    def test_stems_ready_variations(self):
        """stems_ready should handle various truthy values from Redis."""
        for truthy in (True, "True", "true", "1", 1):
            data = {
                "job_id": "t",
                "youtube_url": "u",
                "status": "queued",
                "created_at": "1000",
                "stems_ready": truthy,
            }
            job = Job.from_dict(data)
            assert job.stems_ready is True

        for falsy in (False, "False", "false", "0", 0, None, ""):
            data = {
                "job_id": "t",
                "youtube_url": "u",
                "status": "queued",
                "created_at": "1000",
                "stems_ready": falsy,
            }
            job = Job.from_dict(data)
            assert job.stems_ready is False


class TestJobStatus:
    def test_all_statuses(self):
        expected = {
            "queued", "downloading", "separating", "analyzing",
            "waiting_images", "rendering", "done", "error",
        }
        assert {s.value for s in JobStatus} == expected

    def test_status_string_comparison(self):
        assert JobStatus.QUEUED == "queued"
        assert JobStatus.DONE == "done"


class TestRedisHelpers:
    def test_create_job(self, mock_redis, temp_dir):
        from app.models import create_job
        job = create_job("https://youtube.com/watch?v=test123")
        assert len(job.job_id) == 12
        assert job.youtube_url == "https://youtube.com/watch?v=test123"
        assert job.status == JobStatus.QUEUED
        assert job.dir.exists()

    def test_get_job(self, mock_redis, temp_dir):
        from app.models import create_job, get_job
        original = create_job("https://youtube.com/watch?v=gettest")
        fetched = get_job(original.job_id)
        assert fetched is not None
        assert fetched.job_id == original.job_id
        assert fetched.youtube_url == original.youtube_url

    def test_get_job_not_found(self, mock_redis):
        from app.models import get_job
        assert get_job("nonexistent") is None

    def test_update_job(self, mock_redis, temp_dir):
        from app.models import create_job, update_job, get_job
        job = create_job("https://youtube.com/watch?v=update")
        updated = update_job(job, status=JobStatus.DOWNLOADING, progress=0.5)
        assert updated.status == JobStatus.DOWNLOADING
        assert updated.progress == 0.5
        # Verify persisted in Redis
        fetched = get_job(job.job_id)
        assert fetched.status == JobStatus.DOWNLOADING

    def test_list_jobs(self, mock_redis, temp_dir):
        from app.models import create_job, list_jobs
        create_job("https://youtube.com/watch?v=a")
        create_job("https://youtube.com/watch?v=b")
        ids = list_jobs()
        assert len(ids) == 2
