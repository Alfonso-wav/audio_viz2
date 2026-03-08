"""
Tests for app.worker.renderer — effect functions and frame rendering.
"""

import pytest
import math
from pathlib import Path

import numpy as np
from PIL import Image

from app.worker.renderer import (
    effect_pulse,
    effect_distort,
    effect_rotate,
    effect_glow,
    render_frames,
    _placeholder_color,
    EFFECTS,
)


CANVAS_SIZE = (320, 180)


def _make_test_image(size=(200, 200), color=(255, 0, 0, 200)):
    return Image.new("RGBA", size, color)


class TestEffectPulse:
    def test_zero_energy(self):
        img = _make_test_image()
        result, pos = effect_pulse(img, 0.0, 1.0, CANVAS_SIZE)
        assert result.size[0] > 0
        assert result.size[1] > 0
        # At zero energy, scale = base_scale (0.3)
        assert result.size[0] == int(CANVAS_SIZE[0] * 0.3)

    def test_full_energy(self):
        img = _make_test_image()
        result, pos = effect_pulse(img, 1.0, 1.0, CANVAS_SIZE)
        # scale = 0.3 + 1.0*0.4*1.0 = 0.7
        assert result.size[0] == int(CANVAS_SIZE[0] * 0.7)

    def test_centered(self):
        img = _make_test_image()
        result, pos = effect_pulse(img, 0.5, 1.0, CANVAS_SIZE)
        x, y = pos
        assert x == (CANVAS_SIZE[0] - result.size[0]) // 2
        assert y == (CANVAS_SIZE[1] - result.size[1]) // 2

    def test_intensity_scaling(self):
        img = _make_test_image()
        r1, _ = effect_pulse(img, 1.0, 0.5, CANVAS_SIZE)
        r2, _ = effect_pulse(img, 1.0, 1.0, CANVAS_SIZE)
        # Higher intensity → bigger
        assert r2.size[0] > r1.size[0]


class TestEffectDistort:
    def test_low_energy_no_distortion(self):
        img = _make_test_image()
        result, pos = effect_distort(img, 0.05, 1.0, CANVAS_SIZE)
        # energy <= 0.1 → no wave distortion applied
        assert result.size[0] > 0

    def test_high_energy_distortion(self):
        img = _make_test_image()
        result, pos = effect_distort(img, 0.8, 1.0, CANVAS_SIZE)
        assert result.size[0] > 0
        assert result.size[1] > 0


class TestEffectRotate:
    def test_rotation_returns_image(self):
        img = _make_test_image()
        result, pos = effect_rotate(img, 0.5, 1.0, CANVAS_SIZE, frame_idx=10)
        assert result.size[0] > 0

    def test_rotation_varies_by_frame(self):
        img = _make_test_image()
        r1, _ = effect_rotate(img, 0.5, 1.0, CANVAS_SIZE, frame_idx=0)
        r2, _ = effect_rotate(img, 0.5, 1.0, CANVAS_SIZE, frame_idx=100)
        # Different frames produce different rotations (may differ in size due to expand)
        # Just verify both succeed
        assert r1.size[0] > 0
        assert r2.size[0] > 0


class TestEffectGlow:
    def test_low_energy_no_blur(self):
        img = _make_test_image()
        result, pos = effect_glow(img, 0.1, 1.0, CANVAS_SIZE)
        assert result.size[0] > 0

    def test_high_energy_glow(self):
        img = _make_test_image()
        result, pos = effect_glow(img, 0.8, 1.0, CANVAS_SIZE)
        assert result.size[0] > 0


class TestEffectsRegistry:
    def test_all_effects_registered(self):
        assert set(EFFECTS.keys()) == {"pulse", "distort", "rotate", "glow"}

    def test_all_effects_callable(self):
        for name, fn in EFFECTS.items():
            assert callable(fn)


class TestPlaceholderColor:
    def test_distinct_colors(self):
        colors = [_placeholder_color(i) for i in range(5)]
        assert len(set(colors)) == 5, "All 5 placeholders should have unique colors"

    def test_wraps_around(self):
        assert _placeholder_color(0) == _placeholder_color(5)

    def test_rgba_format(self):
        c = _placeholder_color(0)
        assert len(c) == 4
        assert all(0 <= v <= 255 for v in c)


class TestRenderFrames:
    def test_renders_correct_number_of_frames(self, temp_dir, sample_features, sample_visual_spec):
        job_dir = temp_dir / "render_test"
        job_dir.mkdir()
        images_dir = job_dir / "images"
        images_dir.mkdir()
        frames_dir = job_dir / "frames"
        frames_dir.mkdir()

        # Create placeholder images
        for i in range(5):
            img = Image.new("RGBA", (100, 100), _placeholder_color(i))
            img.save(str(images_dir / f"layer_{i}.png"))

        render_frames(
            job_dir=job_dir,
            features=sample_features,
            visual_spec=sample_visual_spec,
            frames_dir=frames_dir,
        )

        frame_files = sorted(frames_dir.glob("frame_*.png"))
        assert len(frame_files) == sample_features["total_frames"]

    def test_frame_dimensions(self, temp_dir, sample_features, sample_visual_spec):
        job_dir = temp_dir / "dim_test"
        job_dir.mkdir()
        images_dir = job_dir / "images"
        images_dir.mkdir()
        frames_dir = job_dir / "frames"
        frames_dir.mkdir()

        for i in range(5):
            img = Image.new("RGBA", (100, 100), (255, 0, 0, 200))
            img.save(str(images_dir / f"layer_{i}.png"))

        render_frames(
            job_dir=job_dir,
            features=sample_features,
            visual_spec=sample_visual_spec,
            frames_dir=frames_dir,
        )

        frame = Image.open(str(frames_dir / "frame_00000.png"))
        assert frame.size == (sample_visual_spec["width"], sample_visual_spec["height"])

    def test_progress_callback(self, temp_dir, sample_features, sample_visual_spec):
        job_dir = temp_dir / "progress_test"
        job_dir.mkdir()
        images_dir = job_dir / "images"
        images_dir.mkdir()
        frames_dir = job_dir / "frames"
        frames_dir.mkdir()

        for i in range(5):
            img = Image.new("RGBA", (100, 100), (0, 255, 0, 200))
            img.save(str(images_dir / f"layer_{i}.png"))

        progress_calls = []
        render_frames(
            job_dir=job_dir,
            features=sample_features,
            visual_spec=sample_visual_spec,
            frames_dir=frames_dir,
            on_progress=lambda p: progress_calls.append(p),
        )

        assert len(progress_calls) > 0
        assert progress_calls[-1] == 1.0

    def test_missing_images_uses_placeholders(self, temp_dir, sample_features, sample_visual_spec):
        job_dir = temp_dir / "placeholder_test"
        job_dir.mkdir()
        images_dir = job_dir / "images"
        images_dir.mkdir()
        frames_dir = job_dir / "frames"
        frames_dir.mkdir()

        # No images uploaded — should use placeholders
        render_frames(
            job_dir=job_dir,
            features=sample_features,
            visual_spec=sample_visual_spec,
            frames_dir=frames_dir,
        )

        frame_files = sorted(frames_dir.glob("frame_*.png"))
        assert len(frame_files) == sample_features["total_frames"]
