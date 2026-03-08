"""
Tests for app.schemas — Pydantic request/response validation.
"""

import pytest
from pydantic import ValidationError

from app.schemas import CreateJobRequest, JobResponse, ExportRequest, LayerConfig


class TestCreateJobRequest:
    def test_valid_url(self):
        req = CreateJobRequest(youtube_url="https://youtube.com/watch?v=dQw4w9WgXcQ")
        assert req.youtube_url == "https://youtube.com/watch?v=dQw4w9WgXcQ"

    def test_any_string_accepted(self):
        # youtube_url is str, not HttpUrl, so any string is valid
        req = CreateJobRequest(youtube_url="some-string")
        assert req.youtube_url == "some-string"

    def test_missing_url_raises(self):
        with pytest.raises(ValidationError):
            CreateJobRequest()


class TestJobResponse:
    def test_full_response(self):
        resp = JobResponse(
            job_id="abc",
            youtube_url="https://youtube.com/watch?v=x",
            status="queued",
            progress=0.0,
        )
        assert resp.job_id == "abc"
        assert resp.error is None
        assert resp.stems_ready is False

    def test_optional_fields(self):
        resp = JobResponse(
            job_id="abc",
            youtube_url="u",
            status="done",
            progress=1.0,
            error="some error",
            audio_duration=30.0,
            stems_ready=True,
            images_uploaded=5,
        )
        assert resp.error == "some error"
        assert resp.audio_duration == 30.0
        assert resp.images_uploaded == 5


class TestLayerConfig:
    def test_defaults(self):
        layer = LayerConfig(image_index=0, band="low")
        assert layer.effect == "pulse"
        assert layer.intensity == 1.0
        assert layer.blend_mode == "normal"
        assert layer.z_index == 0

    def test_custom_values(self):
        layer = LayerConfig(
            image_index=2,
            band="high",
            effect="rotate",
            intensity=0.5,
            blend_mode="screen",
            z_index=3,
        )
        assert layer.image_index == 2
        assert layer.band == "high"
        assert layer.effect == "rotate"


class TestExportRequest:
    def test_defaults(self):
        req = ExportRequest()
        assert req.preset == "default"
        assert req.layers == []

    def test_with_layers(self):
        req = ExportRequest(
            preset="energetic",
            layers=[
                LayerConfig(image_index=0, band="low"),
                LayerConfig(image_index=1, band="mid", effect="glow"),
            ],
        )
        assert len(req.layers) == 2
        assert req.layers[0].band == "low"
        assert req.layers[1].effect == "glow"

    def test_model_dump(self):
        layer = LayerConfig(image_index=0, band="low")
        d = layer.model_dump()
        assert isinstance(d, dict)
        assert d["image_index"] == 0
        assert d["band"] == "low"
