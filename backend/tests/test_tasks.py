"""
Tests for app.worker.tasks — Celery task logic (mocked externals).
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.models import Job, JobStatus


class TestProcessAudioTask:
    @patch("app.worker.tasks.extract_features")
    @patch("app.worker.tasks.separate_stems")
    @patch("app.worker.tasks.download_audio")
    @patch("app.worker.tasks.update_job")
    @patch("app.worker.tasks.get_job")
    def test_process_audio_pipeline(
        self, mock_get, mock_update, mock_download, mock_separate, mock_extract, temp_dir
    ):
        from app.worker.tasks import process_audio_task

        job = Job(
            job_id="pipe123",
            youtube_url="https://youtube.com/watch?v=test",
            created_at=1000.0,
        )
        job.dir.mkdir(parents=True, exist_ok=True)
        mock_get.return_value = job
        mock_update.return_value = job

        mix_path = job.dir / "mix.wav"
        mix_path.write_bytes(b"fake_audio")
        mock_download.return_value = mix_path

        mock_separate.return_value = {"vocals": mix_path}
        mock_extract.return_value = {
            "duration": 10.0,
            "fps": 30,
            "total_frames": 300,
            "rms": [0.5] * 300,
            "bands": {b: [0.5] * 300 for b in ["low", "low_mid", "mid", "high_mid", "high"]},
        }

        # Call the task function directly (not via Celery)
        process_audio_task("pipe123")

        mock_download.assert_called_once()
        mock_separate.assert_called_once()
        mock_extract.assert_called_once()
        # Features file should be saved
        features_path = job.dir / "features.json"
        assert features_path.exists()

    @patch("app.worker.tasks.download_audio", side_effect=RuntimeError("yt-dlp failed"))
    @patch("app.worker.tasks.update_job")
    @patch("app.worker.tasks.get_job")
    def test_process_audio_error_handling(
        self, mock_get, mock_update, mock_download, temp_dir
    ):
        from app.worker.tasks import process_audio_task

        job = Job(
            job_id="err123",
            youtube_url="https://youtube.com/watch?v=bad",
            created_at=1000.0,
        )
        job.dir.mkdir(parents=True, exist_ok=True)
        mock_get.return_value = job
        mock_update.return_value = job

        with pytest.raises(RuntimeError, match="yt-dlp failed"):
            process_audio_task("err123")

        # update_job should have been called with ERROR status
        error_calls = [
            call for call in mock_update.call_args_list
            if call.kwargs.get("status") == JobStatus.ERROR
        ]
        assert len(error_calls) >= 1

    @patch("app.worker.tasks.get_job")
    def test_process_audio_job_not_found(self, mock_get):
        from app.worker.tasks import process_audio_task

        mock_get.return_value = None
        # Should return early without error
        process_audio_task("nonexistent")


class TestRenderExportTask:
    @patch("app.worker.tasks.subprocess.run")
    @patch("app.worker.tasks.render_frames")
    @patch("app.worker.tasks.update_job")
    @patch("app.worker.tasks.get_job")
    def test_render_pipeline(
        self, mock_get, mock_update, mock_render, mock_ffmpeg, temp_dir
    ):
        from app.worker.tasks import render_export_task

        job = Job(
            job_id="render123",
            youtube_url="https://youtube.com/watch?v=test",
            status=JobStatus.RENDERING,
            created_at=1000.0,
            visual_spec={"fps": 30, "width": 320, "height": 180, "layers": []},
        )
        job.dir.mkdir(parents=True, exist_ok=True)

        # Write features file
        features = {"rms": [0.5] * 10, "bands": {}, "total_frames": 10, "duration": 0.33, "fps": 30}
        with open(job.dir / "features.json", "w") as f:
            json.dump(features, f)

        # Write a dummy mix.wav
        (job.dir / "mix.wav").write_bytes(b"fake_wav")

        mock_get.return_value = job
        mock_update.return_value = job
        mock_ffmpeg.return_value = MagicMock(returncode=0, stderr="", stdout="")

        render_export_task("render123")

        mock_render.assert_called_once()
        mock_ffmpeg.assert_called_once()

    @patch("app.worker.tasks.get_job")
    def test_render_job_not_found(self, mock_get):
        from app.worker.tasks import render_export_task

        mock_get.return_value = None
        render_export_task("nonexistent")


class TestDefaultVisualSpec:
    def test_default_spec_structure(self):
        from app.worker.tasks import _default_visual_spec

        spec = _default_visual_spec()
        assert spec["fps"] == 30
        assert spec["width"] == 1280
        assert spec["height"] == 720
        assert len(spec["layers"]) == 5
        bands = [l["band"] for l in spec["layers"]]
        assert bands == ["low", "low_mid", "mid", "high_mid", "high"]
