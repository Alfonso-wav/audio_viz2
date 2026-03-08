"""
Tests for app.config settings.
"""

import pytest
from pathlib import Path


class TestSettings:
    def test_defaults(self):
        from app.config import settings
        assert settings.max_audio_duration == 60
        assert settings.job_ttl == 3600
        assert settings.video_width == 1280
        assert settings.video_height == 720
        assert settings.video_fps == 30
        assert settings.max_upload_size_mb == 10
        assert settings.max_concurrent_jobs == 4

    def test_temp_dir_is_path(self):
        from app.config import settings
        assert isinstance(settings.temp_dir, Path)
