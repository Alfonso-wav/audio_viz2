"""
Backend test dependencies.
"""

import pytest
import json
import time
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Override settings before importing app modules
import os
os.environ["AUDIOVIZ_REDIS_URL"] = "redis://localhost:6379/15"  # test DB
os.environ["AUDIOVIZ_CELERY_BROKER_URL"] = "redis://localhost:6379/15"
os.environ["AUDIOVIZ_CELERY_RESULT_BACKEND"] = "redis://localhost:6379/15"

_test_temp = tempfile.mkdtemp(prefix="audioviz_test_")
os.environ["AUDIOVIZ_TEMP_DIR"] = _test_temp
