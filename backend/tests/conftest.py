"""
Shared pytest fixtures for backend tests.
"""

import pytest
import json
import time
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import os
os.environ["AUDIOVIZ_REDIS_URL"] = "redis://localhost:6379/15"
os.environ["AUDIOVIZ_TEMP_DIR"] = tempfile.mkdtemp(prefix="audioviz_test_")


@pytest.fixture(autouse=True)
def temp_dir(tmp_path):
    """Override temp_dir for each test to a fresh directory."""
    from app.config import settings
    original = settings.temp_dir
    settings.temp_dir = tmp_path / "audio_viz"
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    yield settings.temp_dir
    settings.temp_dir = original


@pytest.fixture
def mock_redis():
    """Provide a fake Redis that uses a dict in memory."""
    storage = {}
    ttls = {}

    class FakeRedis:
        def hset(self, key, mapping=None, **kwargs):
            if mapping:
                storage[key] = {str(k): str(v) for k, v in mapping.items()}

        def hgetall(self, key):
            return storage.get(key, {})

        def expire(self, key, ttl):
            ttls[key] = ttl

        def keys(self, pattern="*"):
            import fnmatch
            return [k for k in storage if fnmatch.fnmatch(k, pattern)]

        def delete(self, *keys):
            for k in keys:
                storage.pop(k, None)

    fake = FakeRedis()
    with patch("app.models.get_redis", return_value=fake):
        yield fake


@pytest.fixture
def sample_features():
    """A minimal valid features dict."""
    return {
        "duration": 2.0,
        "fps": 30,
        "total_frames": 60,
        "rms": [0.5] * 60,
        "bands": {
            "low": [0.8] * 60,
            "low_mid": [0.6] * 60,
            "mid": [0.4] * 60,
            "high_mid": [0.3] * 60,
            "high": [0.2] * 60,
        },
    }


@pytest.fixture
def sample_visual_spec():
    """A minimal valid visual spec."""
    bands = ["low", "low_mid", "mid", "high_mid", "high"]
    return {
        "fps": 30,
        "width": 320,
        "height": 180,
        "preset": "default",
        "layers": [
            {
                "image_index": i,
                "band": bands[i],
                "effect": "pulse",
                "intensity": 1.0,
                "blend_mode": "normal",
                "z_index": i,
            }
            for i in range(5)
        ],
    }
