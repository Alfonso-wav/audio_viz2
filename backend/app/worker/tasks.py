"""
Celery tasks — the main processing pipeline.

Task 1: process_audio_task
  - Download audio from YouTube (yt-dlp)
  - Separate into 5 stems (Spleeter)
  - Extract audio features (RMS + FFT bands per frame)

Task 2: render_export_task
  - Read visual spec + features
  - Render frames with Pillow
  - Encode MP4 with ffmpeg
"""

from __future__ import annotations

import json
import subprocess
import traceback
from pathlib import Path

from app.celery_app import celery_app
from app.models import get_job, update_job, JobStatus
from app.worker.audio import download_audio, separate_stems, extract_features
from app.worker.renderer import render_frames
from app.config import settings


@celery_app.task(name="process_audio", bind=True, max_retries=1)
def process_audio_task(self, job_id: str):
    """Pipeline: download → separate → analyze."""
    job = get_job(job_id)
    if not job:
        return

    try:
        # ── Step 1: Download ───────────────────────────────
        job = update_job(job, status=JobStatus.DOWNLOADING, progress=0.1)
        mix_path = download_audio(job)

        # ── Step 2: Separate stems ─────────────────────────
        job = update_job(job, status=JobStatus.SEPARATING, progress=0.3)
        separate_stems(job, mix_path)
        job = update_job(job, stems_ready=True, progress=0.6)

        # ── Step 3: Extract features ──────────────────────
        job = update_job(job, status=JobStatus.ANALYZING, progress=0.7)
        features = extract_features(mix_path, fps=settings.video_fps)

        # Save features to disk
        features_path = job.dir / "features.json"
        with open(features_path, "w") as f:
            json.dump(features, f)

        job = update_job(
            job,
            status=JobStatus.WAITING_IMAGES,
            progress=1.0,
            audio_duration=features["duration"],
        )

    except Exception as e:
        update_job(job, status=JobStatus.ERROR, error=str(e))
        traceback.print_exc()
        raise


@celery_app.task(name="render_export", bind=True, max_retries=0)
def render_export_task(self, job_id: str):
    """Pipeline: render frames → ffmpeg encode → done."""
    job = get_job(job_id)
    if not job:
        return

    try:
        job = update_job(job, status=JobStatus.RENDERING, progress=0.0)

        # Load features
        features_path = job.dir / "features.json"
        with open(features_path, "r") as f:
            features = json.load(f)

        # Load visual spec
        visual_spec = job.visual_spec or _default_visual_spec()

        # ── Step 1: Render frames ──────────────────────────
        frames_dir = job.dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        total_frames = len(features["rms"])
        render_frames(
            job_dir=job.dir,
            features=features,
            visual_spec=visual_spec,
            frames_dir=frames_dir,
            on_progress=lambda p: update_job(job, progress=p * 0.8),
        )

        # ── Step 2: FFmpeg encode ──────────────────────────
        job = update_job(job, progress=0.85)
        output_path = job.dir / "output.mp4"
        mix_path = job.dir / "mix.wav"

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(settings.video_fps),
            "-i", str(frames_dir / "frame_%05d.png"),
            "-i", str(mix_path),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]

        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")

        job = update_job(job, status=JobStatus.DONE, progress=1.0)

    except Exception as e:
        update_job(job, status=JobStatus.ERROR, error=str(e))
        traceback.print_exc()
        raise


def _default_visual_spec() -> dict:
    """Fallback visual spec if none provided."""
    bands = ["low", "low_mid", "mid", "high_mid", "high"]
    return {
        "fps": 30,
        "width": 1280,
        "height": 720,
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
