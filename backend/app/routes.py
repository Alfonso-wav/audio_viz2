"""
API Routes for the Audio Visualizer.

Endpoints:
  POST /api/jobs                  → Create job (start YouTube download + separation)
  GET  /api/jobs/{id}             → Get job status
  POST /api/jobs/{id}/images      → Upload images (multipart)
  GET  /api/jobs/{id}/preview-data→ Get audio features for live preview
  GET  /api/jobs/{id}/audio       → Stream the mix audio file
  POST /api/jobs/{id}/export      → Start MP4 render
  GET  /api/jobs/{id}/download    → Download finished MP4
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse

from app.schemas import CreateJobRequest, JobResponse, ExportRequest
from app.models import (
    create_job,
    get_job,
    update_job,
    JobStatus,
)
from app.worker.tasks import process_audio_task, render_export_task

router = APIRouter()

STEM_NAMES = ["vocals", "drums", "bass", "piano", "other"]
BAND_NAMES = ["low", "low_mid", "mid", "high_mid", "high"]


# ── POST /jobs ─────────────────────────────────────────────────

@router.post("/jobs", response_model=JobResponse)
async def create_new_job(req: CreateJobRequest):
    """Create a new job: downloads audio and runs Spleeter separation."""
    job = create_job(req.youtube_url)
    # Dispatch Celery task
    process_audio_task.delay(job.job_id)
    return _job_response(job)


# ── GET /jobs/{id} ─────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    job = _get_or_404(job_id)
    return _job_response(job)


# ── POST /jobs/{id}/images ─────────────────────────────────────

@router.post("/jobs/{job_id}/images", response_model=JobResponse)
async def upload_images(job_id: str, files: List[UploadFile] = File(...)):
    """Upload up to 5 images (one per stem layer)."""
    job = _get_or_404(job_id)

    if len(files) > 5:
        raise HTTPException(400, "Maximum 5 images allowed")

    images_dir = job.dir / "images"
    images_dir.mkdir(exist_ok=True)

    for i, f in enumerate(files):
        ext = Path(f.filename or "img.png").suffix or ".png"
        dest = images_dir / f"layer_{i}{ext}"
        with open(dest, "wb") as out:
            content = await f.read()
            out.write(content)

    job = update_job(job, images_uploaded=len(files), status=JobStatus.WAITING_IMAGES if len(files) < 5 else job.status)
    if len(files) == 5 and job.status == JobStatus.WAITING_IMAGES:
        job = update_job(job, status=JobStatus.ANALYZING)

    return _job_response(job)


# ── GET /jobs/{id}/preview-data ────────────────────────────────

@router.get("/jobs/{job_id}/preview-data")
async def get_preview_data(job_id: str):
    """Return precomputed audio features for the frontend visualizer."""
    job = _get_or_404(job_id)
    features_path = job.dir / "features.json"

    if not features_path.exists():
        raise HTTPException(404, "Features not computed yet")

    with open(features_path, "r") as f:
        features = json.load(f)

    return JSONResponse(content=features)


# ── GET /jobs/{id}/audio ───────────────────────────────────────

@router.get("/jobs/{job_id}/audio")
async def get_audio(job_id: str):
    """Stream the mixed audio file for live preview."""
    job = _get_or_404(job_id)
    audio_path = job.dir / "mix.wav"

    if not audio_path.exists():
        raise HTTPException(404, "Audio not ready yet")

    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename="mix.wav",
    )


# ── POST /jobs/{id}/export ─────────────────────────────────────

@router.post("/jobs/{job_id}/export", response_model=JobResponse)
async def start_export(job_id: str, req: ExportRequest):
    """Start the offline MP4 render pipeline."""
    job = _get_or_404(job_id)

    if job.images_uploaded < 5:
        raise HTTPException(400, "Upload 5 images before exporting")

    # Build visual spec
    visual_spec = {
        "fps": 30,
        "width": 1280,
        "height": 720,
        "preset": req.preset,
        "layers": [l.model_dump() for l in req.layers],
    }

    job = update_job(job, status=JobStatus.RENDERING, progress=0.0, visual_spec=visual_spec)

    # Dispatch render task
    render_export_task.delay(job.job_id)

    return _job_response(job)


# ── GET /jobs/{id}/download ────────────────────────────────────

@router.get("/jobs/{job_id}/download")
async def download_video(job_id: str):
    """Download the finished MP4 video."""
    job = _get_or_404(job_id)

    if job.status != JobStatus.DONE:
        raise HTTPException(400, f"Job not done yet. Status: {job.status.value}")

    mp4_path = job.dir / "output.mp4"
    if not mp4_path.exists():
        raise HTTPException(404, "MP4 file not found")

    return FileResponse(
        mp4_path,
        media_type="video/mp4",
        filename=f"visualizer_{job_id}.mp4",
    )


# ── Helpers ────────────────────────────────────────────────────

def _get_or_404(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, f"Job {job_id} not found")
    return job


def _job_response(job) -> JobResponse:
    return JobResponse(
        job_id=job.job_id,
        youtube_url=job.youtube_url,
        status=job.status.value,
        progress=job.progress,
        error=job.error,
        audio_duration=job.audio_duration,
        stems_ready=job.stems_ready,
        images_uploaded=job.images_uploaded,
    )
