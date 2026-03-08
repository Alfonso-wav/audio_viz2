"""
Automatic cleanup of expired job files.
Runs as a background thread in the FastAPI process.
"""

from __future__ import annotations

import shutil
import time
import threading
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL = 300  # Run every 5 minutes


def _cleanup_loop():
    """Delete job directories older than job_ttl seconds."""
    while True:
        try:
            time.sleep(CLEANUP_INTERVAL)
            now = time.time()
            temp_dir = settings.temp_dir

            if not temp_dir.exists():
                continue

            for job_dir in temp_dir.iterdir():
                if not job_dir.is_dir():
                    continue

                # Use directory modification time as proxy for job age
                dir_age = now - job_dir.stat().st_mtime
                if dir_age > settings.job_ttl:
                    logger.info(f"Cleaning up expired job: {job_dir.name}")
                    shutil.rmtree(str(job_dir), ignore_errors=True)

        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def start_cleanup_scheduler():
    """Start the cleanup thread (daemon, dies with main process)."""
    thread = threading.Thread(target=_cleanup_loop, daemon=True, name="cleanup")
    thread.start()
    logger.info("Cleanup scheduler started")
