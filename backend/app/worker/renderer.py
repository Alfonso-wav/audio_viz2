"""
Offline frame renderer using Pillow.

Renders PNG frames deterministically based on:
  - Audio features (RMS + frequency bands per frame)
  - Visual spec (layer config, preset, effects)
  - User-uploaded images

Effects per layer:
  - pulse: scale image based on band energy
  - distort: wave distortion based on band energy
  - rotate: rotation based on band energy
  - glow: brightness/opacity modulation

This mirrors the p5.js frontend logic for deterministic parity.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw


# ── Effect functions ───────────────────────────────────────────

def effect_pulse(img: Image.Image, energy: float, intensity: float, canvas_size: tuple) -> tuple[Image.Image, tuple]:
    """Scale image based on energy. Returns (image, paste_position)."""
    base_scale = 0.3
    scale = base_scale + energy * 0.4 * intensity
    w = int(canvas_size[0] * scale)
    h = int(canvas_size[1] * scale)
    if w < 1 or h < 1:
        w, h = 1, 1
    resized = img.resize((w, h), Image.LANCZOS)
    x = (canvas_size[0] - w) // 2
    y = (canvas_size[1] - h) // 2
    return resized, (x, y)


def effect_distort(img: Image.Image, energy: float, intensity: float, canvas_size: tuple) -> tuple[Image.Image, tuple]:
    """Wave distortion based on energy."""
    base_scale = 0.35
    scale = base_scale + energy * 0.2 * intensity
    w = int(canvas_size[0] * scale)
    h = int(canvas_size[1] * scale)
    if w < 1 or h < 1:
        w, h = 1, 1
    resized = img.resize((w, h), Image.LANCZOS)

    # Apply wave distortion
    if energy > 0.1:
        amplitude = int(energy * 10 * intensity)
        arr = np.array(resized)
        for row in range(arr.shape[0]):
            shift = int(amplitude * math.sin(2 * math.pi * row / max(arr.shape[0], 1) * 3))
            arr[row] = np.roll(arr[row], shift, axis=0)
        resized = Image.fromarray(arr)

    x = (canvas_size[0] - w) // 2
    y = (canvas_size[1] - h) // 2
    return resized, (x, y)


def effect_rotate(img: Image.Image, energy: float, intensity: float, canvas_size: tuple, frame_idx: int = 0) -> tuple[Image.Image, tuple]:
    """Rotation based on cumulative energy."""
    base_scale = 0.3
    scale = base_scale + energy * 0.2 * intensity
    w = int(canvas_size[0] * scale)
    h = int(canvas_size[1] * scale)
    if w < 1 or h < 1:
        w, h = 1, 1
    resized = img.resize((w, h), Image.LANCZOS)

    angle = frame_idx * 0.5 * intensity + energy * 30 * intensity
    rotated = resized.rotate(angle, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))

    x = (canvas_size[0] - rotated.width) // 2
    y = (canvas_size[1] - rotated.height) // 2
    return rotated, (x, y)


def effect_glow(img: Image.Image, energy: float, intensity: float, canvas_size: tuple) -> tuple[Image.Image, tuple]:
    """Brightness/glow modulation."""
    base_scale = 0.35
    scale = base_scale + energy * 0.3 * intensity
    w = int(canvas_size[0] * scale)
    h = int(canvas_size[1] * scale)
    if w < 1 or h < 1:
        w, h = 1, 1
    resized = img.resize((w, h), Image.LANCZOS)

    # Brighten based on energy
    enhancer = ImageEnhance.Brightness(resized)
    brightened = enhancer.enhance(1.0 + energy * 1.5 * intensity)

    # Add blur glow
    if energy > 0.3:
        glow = brightened.filter(ImageFilter.GaussianBlur(radius=int(energy * 8)))
        brightened = Image.blend(brightened, glow, energy * 0.3)

    x = (canvas_size[0] - w) // 2
    y = (canvas_size[1] - h) // 2
    return brightened, (x, y)


EFFECTS = {
    "pulse": effect_pulse,
    "distort": effect_distort,
    "rotate": effect_rotate,
    "glow": effect_glow,
}


# ── Main render pipeline ──────────────────────────────────────

def render_frames(
    job_dir: Path,
    features: dict,
    visual_spec: dict,
    frames_dir: Path,
    on_progress: Optional[Callable[[float], None]] = None,
):
    """
    Render all frames as PNGs to frames_dir.

    Args:
        job_dir: Job working directory (contains images/)
        features: Audio features dict (rms, bands)
        visual_spec: Visual spec dict (layers, preset, resolution)
        frames_dir: Output directory for frame PNGs
        on_progress: Callback with progress 0.0-1.0
    """
    width = visual_spec.get("width", 1280)
    height = visual_spec.get("height", 720)
    canvas_size = (width, height)
    total_frames = features["total_frames"]
    layers = visual_spec.get("layers", [])

    # Load images
    images_dir = job_dir / "images"
    layer_images = []
    for i in range(5):
        # Find the image file for this layer
        candidates = list(images_dir.glob(f"layer_{i}.*"))
        if candidates:
            img = Image.open(str(candidates[0])).convert("RGBA")
            layer_images.append(img)
        else:
            # Create a placeholder colored rectangle
            placeholder = Image.new("RGBA", (200, 200), _placeholder_color(i))
            layer_images.append(placeholder)

    # Sort layers by z_index
    sorted_layers = sorted(layers, key=lambda l: l.get("z_index", 0))

    # Render each frame
    for frame_idx in range(total_frames):
        canvas = Image.new("RGBA", canvas_size, (10, 10, 15, 255))

        # Draw background gradient (subtle)
        rms_val = features["rms"][frame_idx] if frame_idx < len(features["rms"]) else 0
        _draw_background(canvas, rms_val, frame_idx)

        for layer_cfg in sorted_layers:
            img_idx = layer_cfg.get("image_index", 0)
            band = layer_cfg.get("band", "mid")
            effect_name = layer_cfg.get("effect", "pulse")
            intensity = layer_cfg.get("intensity", 1.0)

            if img_idx >= len(layer_images):
                continue

            src_img = layer_images[img_idx].copy()

            # Get band energy for this frame
            band_data = features["bands"].get(band, features["rms"])
            energy = band_data[frame_idx] if frame_idx < len(band_data) else 0

            # Apply effect
            effect_fn = EFFECTS.get(effect_name, effect_pulse)
            if effect_name == "rotate":
                result_img, pos = effect_fn(src_img, energy, intensity, canvas_size, frame_idx)
            else:
                result_img, pos = effect_fn(src_img, energy, intensity, canvas_size)

            # Apply opacity based on energy
            opacity = max(0.3, min(1.0, 0.4 + energy * 0.8))
            if result_img.mode == "RGBA":
                r, g, b, a = result_img.split()
                a = a.point(lambda x: int(x * opacity))
                result_img = Image.merge("RGBA", (r, g, b, a))

            # Composite onto canvas
            canvas.paste(result_img, pos, result_img)

        # Save frame
        frame_path = frames_dir / f"frame_{frame_idx:05d}.png"
        canvas.convert("RGB").save(str(frame_path), "PNG", optimize=False)

        # Progress callback
        if on_progress and frame_idx % 10 == 0:
            on_progress(frame_idx / total_frames)

    if on_progress:
        on_progress(1.0)


def _draw_background(canvas: Image.Image, rms: float, frame_idx: int):
    """Draw a subtle animated background."""
    draw = ImageDraw.Draw(canvas)
    w, h = canvas.size

    # Dark base with subtle color shift based on rms
    r = int(10 + rms * 30)
    g = int(10 + rms * 15)
    b = int(20 + rms * 40)

    for y in range(0, h, 4):
        t = y / h
        cr = int(r * (1 - t * 0.5))
        cg = int(g * (1 - t * 0.3))
        cb = int(b * (1 - t * 0.2))
        draw.rectangle([(0, y), (w, y + 4)], fill=(cr, cg, cb))


def _placeholder_color(index: int) -> tuple:
    """Generate a distinct RGBA color for placeholder images."""
    colors = [
        (255, 60, 60, 200),    # red
        (60, 255, 60, 200),    # green
        (60, 120, 255, 200),   # blue
        (255, 200, 60, 200),   # yellow
        (200, 60, 255, 200),   # purple
    ]
    return colors[index % len(colors)]
