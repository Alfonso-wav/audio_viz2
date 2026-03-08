"""
Tests for app.cleanup module.
"""

import time
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch


class TestCleanup:
    def test_start_cleanup_scheduler_starts_thread(self):
        from app.cleanup import start_cleanup_scheduler
        import threading

        initial_threads = {t.name for t in threading.enumerate()}
        start_cleanup_scheduler()
        time.sleep(0.1)
        current_threads = {t.name for t in threading.enumerate()}
        assert "cleanup" in current_threads
