"""
Tests for API routes (app.routes).
Uses FastAPI TestClient with mocked Redis and Celery tasks.
"""

import json
import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.models import Job, JobStatus


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def fake_job(temp_dir):
    """Create a fake Job in known state."""
    job = Job(
        job_id="testjob123",
        youtube_url="https://youtube.com/watch?v=test",
        status=JobStatus.WAITING_IMAGES,
        progress=1.0,
        created_at=1000.0,
        stems_ready=True,
    )
    job.dir.mkdir(parents=True, exist_ok=True)
    return job


class TestCreateJob:
    @patch("app.routes.process_audio_task")
    @patch("app.routes.create_job")
    def test_create_job_success(self, mock_create, mock_task, client):
        mock_job = Job(
            job_id="new123",
            youtube_url="https://youtube.com/watch?v=abc",
            created_at=1000.0,
        )
        mock_create.return_value = mock_job
        mock_task.delay = MagicMock()

        resp = client.post("/api/jobs", json={"youtube_url": "https://youtube.com/watch?v=abc"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == "new123"
        assert data["status"] == "queued"
        mock_task.delay.assert_called_once_with("new123")

    def test_create_job_missing_url(self, client):
        resp = client.post("/api/jobs", json={})
        assert resp.status_code == 422  # Validation error


class TestGetJobStatus:
    @patch("app.routes.get_job")
    def test_get_existing_job(self, mock_get, client):
        mock_get.return_value = Job(
            job_id="exists123",
            youtube_url="https://youtube.com/watch?v=x",
            status=JobStatus.DOWNLOADING,
            progress=0.3,
            created_at=1000.0,
        )
        resp = client.get("/api/jobs/exists123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == "exists123"
        assert data["status"] == "downloading"
        assert data["progress"] == 0.3

    @patch("app.routes.get_job")
    def test_get_nonexistent_job(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/jobs/nope")
        assert resp.status_code == 404


class TestUploadImages:
    @patch("app.routes.update_job")
    @patch("app.routes.get_job")
    def test_upload_5_images(self, mock_get, mock_update, client, fake_job):
        mock_get.return_value = fake_job
        mock_update.return_value = fake_job

        files = [
            ("files", (f"img{i}.png", io.BytesIO(b"\x89PNG" + b"\x00" * 100), "image/png"))
            for i in range(5)
        ]
        resp = client.post(f"/api/jobs/{fake_job.job_id}/images", files=files)
        assert resp.status_code == 200
        mock_update.assert_called()

    @patch("app.routes.get_job")
    def test_upload_too_many_images(self, mock_get, client, fake_job):
        mock_get.return_value = fake_job
        files = [
            ("files", (f"img{i}.png", io.BytesIO(b"\x89PNG" + b"\x00" * 100), "image/png"))
            for i in range(6)
        ]
        resp = client.post(f"/api/jobs/{fake_job.job_id}/images", files=files)
        assert resp.status_code == 400

    @patch("app.routes.get_job")
    def test_upload_images_saves_to_disk(self, mock_get, client, fake_job):
        mock_get.return_value = fake_job
        content = b"\x89PNG_test_data"
        files = [
            ("files", ("test.png", io.BytesIO(content), "image/png")),
        ]

        with patch("app.routes.update_job", return_value=fake_job):
            resp = client.post(f"/api/jobs/{fake_job.job_id}/images", files=files)
            assert resp.status_code == 200

        images_dir = fake_job.dir / "images"
        assert images_dir.exists()
        saved = list(images_dir.glob("layer_0*"))
        assert len(saved) == 1

    @patch("app.routes.get_job")
    def test_upload_images_job_not_found(self, mock_get, client):
        mock_get.return_value = None
        files = [("files", ("img.png", io.BytesIO(b"\x89PNG"), "image/png"))]
        resp = client.post("/api/jobs/nope/images", files=files)
        assert resp.status_code == 404


class TestGetPreviewData:
    @patch("app.routes.get_job")
    def test_get_preview_data(self, mock_get, client, fake_job, sample_features):
        mock_get.return_value = fake_job
        features_path = fake_job.dir / "features.json"
        with open(features_path, "w") as f:
            json.dump(sample_features, f)

        resp = client.get(f"/api/jobs/{fake_job.job_id}/preview-data")
        assert resp.status_code == 200
        data = resp.json()
        assert "rms" in data
        assert "bands" in data
        assert data["fps"] == 30

    @patch("app.routes.get_job")
    def test_get_preview_data_not_ready(self, mock_get, client, fake_job):
        mock_get.return_value = fake_job
        resp = client.get(f"/api/jobs/{fake_job.job_id}/preview-data")
        assert resp.status_code == 404


class TestGetAudio:
    @patch("app.routes.get_job")
    def test_get_audio(self, mock_get, client, fake_job):
        mock_get.return_value = fake_job
        mix_path = fake_job.dir / "mix.wav"
        mix_path.write_bytes(b"RIFF" + b"\x00" * 100)

        resp = client.get(f"/api/jobs/{fake_job.job_id}/audio")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"

    @patch("app.routes.get_job")
    def test_get_audio_not_ready(self, mock_get, client, fake_job):
        mock_get.return_value = fake_job
        resp = client.get(f"/api/jobs/{fake_job.job_id}/audio")
        assert resp.status_code == 404


class TestStartExport:
    @patch("app.routes.render_export_task")
    @patch("app.routes.update_job")
    @patch("app.routes.get_job")
    def test_start_export_success(self, mock_get, mock_update, mock_task, client, fake_job):
        fake_job.images_uploaded = 5
        mock_get.return_value = fake_job
        mock_update.return_value = fake_job
        mock_task.delay = MagicMock()

        body = {
            "preset": "default",
            "layers": [
                {"image_index": i, "band": b, "effect": "pulse", "intensity": 1.0, "blend_mode": "normal", "z_index": i}
                for i, b in enumerate(["low", "low_mid", "mid", "high_mid", "high"])
            ],
        }
        resp = client.post(f"/api/jobs/{fake_job.job_id}/export", json=body)
        assert resp.status_code == 200
        mock_task.delay.assert_called_once_with(fake_job.job_id)

    @patch("app.routes.get_job")
    def test_start_export_without_images(self, mock_get, client, fake_job):
        fake_job.images_uploaded = 3
        mock_get.return_value = fake_job

        body = {"preset": "default", "layers": []}
        resp = client.post(f"/api/jobs/{fake_job.job_id}/export", json=body)
        assert resp.status_code == 400


class TestDownloadVideo:
    @patch("app.routes.get_job")
    def test_download_done(self, mock_get, client, fake_job):
        fake_job.status = JobStatus.DONE
        mock_get.return_value = fake_job
        mp4_path = fake_job.dir / "output.mp4"
        mp4_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")

        resp = client.get(f"/api/jobs/{fake_job.job_id}/download")
        assert resp.status_code == 200
        assert "video/mp4" in resp.headers["content-type"]

    @patch("app.routes.get_job")
    def test_download_not_done(self, mock_get, client, fake_job):
        fake_job.status = JobStatus.RENDERING
        mock_get.return_value = fake_job
        resp = client.get(f"/api/jobs/{fake_job.job_id}/download")
        assert resp.status_code == 400

    @patch("app.routes.get_job")
    def test_download_mp4_missing(self, mock_get, client, fake_job):
        fake_job.status = JobStatus.DONE
        mock_get.return_value = fake_job
        resp = client.get(f"/api/jobs/{fake_job.job_id}/download")
        assert resp.status_code == 404


class TestVersionsEndpoint:
    """Tests for GET and POST /api/versions."""

    def test_versions_returns_data(self, client):
        resp = client.get("/api/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_versions_has_current_key(self, client):
        resp = client.get("/api/versions")
        data = resp.json()
        if data:
            assert "current" in data
            assert "versions" in data

    def test_create_version(self, client, tmp_path):
        """POST /api/versions should create a new version entry."""
        import app.main as main_mod
        import json
        # Point _versions_file to a temp file
        tmp_vf = tmp_path / "versions.json"
        tmp_vf.write_text(json.dumps({
            "current": "0.1.0",
            "versions": [{"version": "0.1.0", "date": "2026-01-01", "description": "Init", "changes": ["A"]}],
        }))
        original_vf = main_mod._versions_file
        main_mod._versions_file = tmp_vf

        try:
            resp = client.post("/api/versions", json={
                "version": "0.2.0",
                "description": "Second release",
                "changes": ["Feature X", "Bug fix Y"],
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["current"] == "0.2.0"
            assert len(data["versions"]) == 2
            assert data["versions"][0]["version"] == "0.2.0"
        finally:
            main_mod._versions_file = original_vf

    def test_create_duplicate_version_409(self, client, tmp_path):
        """POST /api/versions with existing version should return 409."""
        import app.main as main_mod
        import json
        tmp_vf = tmp_path / "versions.json"
        tmp_vf.write_text(json.dumps({
            "current": "0.1.0",
            "versions": [{"version": "0.1.0", "date": "2026-01-01", "description": "Init", "changes": ["A"]}],
        }))
        original_vf = main_mod._versions_file
        main_mod._versions_file = tmp_vf

        try:
            resp = client.post("/api/versions", json={
                "version": "0.1.0",
                "description": "Duplicate!",
                "changes": [],
            })
            assert resp.status_code == 409
            assert "already exists" in resp.json()["detail"]
        finally:
            main_mod._versions_file = original_vf

    def test_create_version_empty_version_string(self, client, tmp_path):
        """POST with empty version string should return 422."""
        import app.main as main_mod
        import json
        tmp_vf = tmp_path / "versions.json"
        tmp_vf.write_text(json.dumps({"current": "0.1.0", "versions": []}))
        original_vf = main_mod._versions_file
        main_mod._versions_file = tmp_vf

        try:
            resp = client.post("/api/versions", json={
                "version": "  ",
                "description": "Empty ver",
                "changes": [],
            })
            assert resp.status_code == 422
        finally:
            main_mod._versions_file = original_vf

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
