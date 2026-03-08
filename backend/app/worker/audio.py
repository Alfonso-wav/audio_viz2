"""
Audio processing utilities:
  - download_audio: yt-dlp download
  - separate_stems: Spleeter 5-stem separation
  - extract_features: RMS + FFT band analysis at 30fps
"""

from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import Optional

import numpy as np
import librosa
import soundfile as sf

from app.config import settings


# ── Band definitions (Hz) ──────────────────────────────────────
# Maps to: low, low_mid, mid, high_mid, high
BAND_EDGES = [0, 200, 800, 2500, 6000, 20000]
BAND_NAMES = ["low", "low_mid", "mid", "high_mid", "high"]


def download_audio(job) -> Path:
    """
    Download audio from YouTube URL using yt-dlp.
    Returns path to mix.wav (mono, 44100 Hz).
    """
    output_template = str(job.dir / "raw_audio.%(ext)s")
    mix_path = job.dir / "mix.wav"

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--output", output_template,
        "--max-filesize", "50M",
        "--socket-timeout", "30",
        job.youtube_url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr[-500:]}")

    # Find the downloaded wav file
    wav_files = list(job.dir.glob("raw_audio*.wav"))
    if not wav_files:
        raise RuntimeError("yt-dlp did not produce a WAV file")

    raw_path = wav_files[0]

    # Convert to mono, 44100Hz, and trim to max duration
    y, sr = librosa.load(str(raw_path), sr=44100, mono=True, duration=settings.max_audio_duration)
    sf.write(str(mix_path), y, 44100)

    # Clean up raw file
    raw_path.unlink(missing_ok=True)

    return mix_path


def separate_stems(job, mix_path: Path) -> dict[str, Path]:
    """
    Run Spleeter 5stems separation.
    Returns dict mapping stem name → wav path.
    """
    output_dir = job.dir / "stems"
    output_dir.mkdir(exist_ok=True)

    cmd = [
        "spleeter", "separate",
        "-p", "spleeter:5stems",
        "-o", str(output_dir),
        str(mix_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"Spleeter failed: {result.stderr[-500:]}")

    # Spleeter outputs to output_dir/mix/vocals.wav, etc.
    stem_dir = output_dir / "mix"
    if not stem_dir.exists():
        # Try to find the actual output dir
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        if subdirs:
            stem_dir = subdirs[0]
        else:
            raise RuntimeError("Spleeter output directory not found")

    stems = {}
    for name in ["vocals", "drums", "bass", "piano", "other"]:
        stem_path = stem_dir / f"{name}.wav"
        if stem_path.exists():
            stems[name] = stem_path

    return stems


def extract_features(mix_path: Path, fps: int = 30) -> dict:
    """
    Extract audio features at `fps` frames per second.

    Returns JSON-serializable dict:
    {
        "duration": float,
        "fps": int,
        "total_frames": int,
        "rms": [float, ...],            # per-frame RMS (0-1 normalized)
        "bands": {
            "low": [float, ...],         # per-frame energy per band (0-1)
            "low_mid": [...],
            "mid": [...],
            "high_mid": [...],
            "high": [...]
        }
    }
    """
    y, sr = librosa.load(str(mix_path), sr=44100, mono=True)
    duration = len(y) / sr
    hop_length = sr // fps  # samples per frame

    # ── RMS per frame ──────────────────────────────────────
    rms = librosa.feature.rms(y=y, frame_length=hop_length * 2, hop_length=hop_length)[0]
    rms_max = rms.max() if rms.max() > 0 else 1.0
    rms_normalized = (rms / rms_max).tolist()

    # ── STFT for frequency bands ──────────────────────────
    n_fft = 2048
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    bands = {}
    for i, name in enumerate(BAND_NAMES):
        lo = BAND_EDGES[i]
        hi = BAND_EDGES[i + 1]

        # Find frequency bin indices for this band
        mask = (freqs >= lo) & (freqs < hi)
        if mask.sum() == 0:
            bands[name] = [0.0] * len(rms_normalized)
            continue

        band_energy = S[mask, :].mean(axis=0)
        band_max = band_energy.max() if band_energy.max() > 0 else 1.0
        bands[name] = (band_energy / band_max).tolist()

    # Ensure all arrays have the same length
    min_len = min(len(rms_normalized), *(len(v) for v in bands.values()))
    rms_normalized = rms_normalized[:min_len]
    bands = {k: v[:min_len] for k, v in bands.items()}

    return {
        "duration": round(duration, 3),
        "fps": fps,
        "total_frames": min_len,
        "rms": rms_normalized,
        "bands": bands,
    }
