"""
Pydantic schemas for request / response validation.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, HttpUrl


class CreateJobRequest(BaseModel):
    youtube_url: str


class JobResponse(BaseModel):
    job_id: str
    youtube_url: str
    status: str
    progress: float
    error: Optional[str] = None
    audio_duration: Optional[float] = None
    stems_ready: bool = False
    images_uploaded: int = 0


class ExportRequest(BaseModel):
    """Visual spec sent from the frontend to start rendering."""
    preset: str = "default"
    layers: list[LayerConfig] = []


class LayerConfig(BaseModel):
    image_index: int  # 0-4
    band: str  # low, low_mid, mid, high_mid, high
    effect: str = "pulse"  # pulse, distort, rotate, scale
    intensity: float = 1.0
    blend_mode: str = "normal"
    z_index: int = 0


# Allow forward ref resolution
ExportRequest.model_rebuild()
