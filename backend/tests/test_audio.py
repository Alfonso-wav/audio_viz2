"""
Tests for app.worker.audio — extract_features with synthetic audio.
(download_audio and separate_stems require external tools, so only feature extraction is tested.)
"""

import pytest
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch

import soundfile as sf

from app.worker.audio import extract_features, BAND_NAMES, BAND_EDGES


@pytest.fixture
def sine_wav(tmp_path):
    """Generate a 2-second sine wave WAV at 440 Hz."""
    sr = 44100
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    path = tmp_path / "test_sine.wav"
    sf.write(str(path), y, sr)
    return path


@pytest.fixture
def silence_wav(tmp_path):
    """Generate a 1-second silence WAV."""
    sr = 44100
    y = np.zeros(sr, dtype=np.float32)
    path = tmp_path / "silence.wav"
    sf.write(str(path), y, sr)
    return path


@pytest.fixture
def low_freq_wav(tmp_path):
    """Generate a 2-second WAV with 100 Hz bass tone."""
    sr = 44100
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = 0.8 * np.sin(2 * np.pi * 100 * t).astype(np.float32)
    path = tmp_path / "bass.wav"
    sf.write(str(path), y, sr)
    return path


class TestExtractFeatures:
    def test_structure(self, sine_wav):
        features = extract_features(sine_wav, fps=30)
        assert "duration" in features
        assert "fps" in features
        assert "total_frames" in features
        assert "rms" in features
        assert "bands" in features
        assert features["fps"] == 30

    def test_duration(self, sine_wav):
        features = extract_features(sine_wav, fps=30)
        assert abs(features["duration"] - 2.0) < 0.1

    def test_total_frames_matches(self, sine_wav):
        features = extract_features(sine_wav, fps=30)
        assert len(features["rms"]) == features["total_frames"]
        for band in BAND_NAMES:
            assert len(features["bands"][band]) == features["total_frames"]

    def test_all_bands_present(self, sine_wav):
        features = extract_features(sine_wav, fps=30)
        for name in BAND_NAMES:
            assert name in features["bands"]

    def test_rms_normalized(self, sine_wav):
        features = extract_features(sine_wav, fps=30)
        rms = features["rms"]
        assert max(rms) <= 1.0 + 1e-6, "RMS should be normalized to [0,1]"
        assert min(rms) >= 0.0

    def test_band_values_normalized(self, sine_wav):
        features = extract_features(sine_wav, fps=30)
        for band_name in BAND_NAMES:
            vals = features["bands"][band_name]
            if max(vals) > 0:
                assert max(vals) <= 1.0 + 1e-6

    def test_silence_produces_low_rms(self, silence_wav):
        features = extract_features(silence_wav, fps=30)
        rms = features["rms"]
        # All silence → RMS should be very low (or all zeros)
        assert max(rms) < 0.01 or all(v == 0 for v in rms)

    def test_sine440_energy_in_mid_band(self, sine_wav):
        """440 Hz falls in the low_mid band (200-800 Hz), so low_mid should have significant energy."""
        features = extract_features(sine_wav, fps=10)
        low_mid = features["bands"]["low_mid"]
        avg_low_mid = sum(low_mid) / len(low_mid) if low_mid else 0
        # 440 Hz is in the low_mid range, should have meaningful energy
        assert avg_low_mid > 0.01

    def test_bass_tone_in_low_band(self, low_freq_wav):
        """100 Hz should appear in the 'low' band (0-200 Hz)."""
        features = extract_features(low_freq_wav, fps=10)
        low = features["bands"]["low"]
        high = features["bands"]["high"]
        avg_low = sum(low) / len(low) if low else 0
        avg_high = sum(high) / len(high) if high else 0
        assert avg_low > avg_high

    def test_different_fps(self, sine_wav):
        f10 = extract_features(sine_wav, fps=10)
        f30 = extract_features(sine_wav, fps=30)
        assert f10["total_frames"] < f30["total_frames"]
        assert f10["fps"] == 10
        assert f30["fps"] == 30

    def test_json_serializable(self, sine_wav):
        features = extract_features(sine_wav, fps=30)
        # Should not raise
        serialized = json.dumps(features)
        restored = json.loads(serialized)
        assert restored["fps"] == 30


class TestBandDefinitions:
    def test_band_names_count(self):
        assert len(BAND_NAMES) == 5

    def test_band_edges_count(self):
        assert len(BAND_EDGES) == 6

    def test_bands_cover_spectrum(self):
        assert BAND_EDGES[0] == 0
        assert BAND_EDGES[-1] == 20000

    def test_band_edges_ascending(self):
        for i in range(len(BAND_EDGES) - 1):
            assert BAND_EDGES[i] < BAND_EDGES[i + 1]
