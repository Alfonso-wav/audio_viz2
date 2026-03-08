"""
Tests for the version.py CLI script (project root).
Tests the load/save/update logic without touching real project files.
"""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch


# The script lives at project root (parent of backend/)
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import version as version_mod


@pytest.fixture
def tmp_versions_file(tmp_path):
    """Create a temp versions.json and point the module to it."""
    vf = tmp_path / "versions.json"
    initial = {
        "current": "0.1.0",
        "versions": [
            {
                "version": "0.1.0",
                "date": "2026-01-01",
                "description": "Initial",
                "changes": ["First release"],
            }
        ],
    }
    vf.write_text(json.dumps(initial, indent=2), encoding="utf-8")
    return vf


class TestLoadVersions:
    def test_load_existing(self, tmp_versions_file):
        with patch.object(version_mod, "VERSIONS_FILE", tmp_versions_file):
            data = version_mod.load_versions()
            assert data["current"] == "0.1.0"
            assert len(data["versions"]) == 1

    def test_load_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        with patch.object(version_mod, "VERSIONS_FILE", missing):
            data = version_mod.load_versions()
            assert data["current"] == "0.0.0"
            assert data["versions"] == []


class TestSaveVersions:
    def test_save_roundtrip(self, tmp_path):
        vf = tmp_path / "v.json"
        with patch.object(version_mod, "VERSIONS_FILE", vf):
            version_mod.save_versions({"current": "1.0.0", "versions": []})
            loaded = json.loads(vf.read_text(encoding="utf-8"))
            assert loaded["current"] == "1.0.0"


class TestUpdateBackendVersion:
    def test_updates_version_string(self, tmp_path):
        main_py = tmp_path / "main.py"
        main_py.write_text('app = FastAPI(version="0.1.0")\n', encoding="utf-8")
        with patch.object(version_mod, "BACKEND_MAIN", main_py):
            version_mod.update_backend_version("2.0.0")
            content = main_py.read_text(encoding="utf-8")
            assert 'version="2.0.0"' in content

    def test_missing_file_skips(self, tmp_path):
        missing = tmp_path / "nope.py"
        with patch.object(version_mod, "BACKEND_MAIN", missing):
            version_mod.update_backend_version("1.0.0")  # Should not raise


class TestUpdateFrontendVersion:
    def test_updates_package_json(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({"name": "test", "version": "0.1.0"}), encoding="utf-8")
        with patch.object(version_mod, "FRONTEND_PACKAGE", pkg):
            version_mod.update_frontend_version("3.0.0")
            data = json.loads(pkg.read_text(encoding="utf-8"))
            assert data["version"] == "3.0.0"

    def test_missing_file_skips(self, tmp_path):
        missing = tmp_path / "nope.json"
        with patch.object(version_mod, "FRONTEND_PACKAGE", missing):
            version_mod.update_frontend_version("1.0.0")  # Should not raise


class TestCmdNew:
    def test_adds_new_version(self, tmp_versions_file, tmp_path):
        # Mock all paths to use temp files
        fake_main = tmp_path / "app" / "main.py"
        fake_main.parent.mkdir(parents=True)
        fake_main.write_text('app = FastAPI(version="0.1.0")\n', encoding="utf-8")

        fake_pkg = tmp_path / "package.json"
        fake_pkg.write_text(json.dumps({"version": "0.1.0"}), encoding="utf-8")

        with (
            patch.object(version_mod, "VERSIONS_FILE", tmp_versions_file),
            patch.object(version_mod, "BACKEND_MAIN", fake_main),
            patch.object(version_mod, "FRONTEND_PACKAGE", fake_pkg),
            patch.object(version_mod, "ROOT", tmp_path),
        ):
            version_mod.cmd_new("0.2.0", "Second release", ["Change A", "Change B"])

            data = json.loads(tmp_versions_file.read_text(encoding="utf-8"))
            assert data["current"] == "0.2.0"
            assert len(data["versions"]) == 2
            assert data["versions"][0]["version"] == "0.2.0"  # newest first
            assert data["versions"][0]["changes"] == ["Change A", "Change B"]

    def test_duplicate_version_exits(self, tmp_versions_file, tmp_path):
        with (
            patch.object(version_mod, "VERSIONS_FILE", tmp_versions_file),
        ):
            with pytest.raises(SystemExit):
                version_mod.cmd_new("0.1.0", "Duplicate!", [])


class TestCmdCurrent:
    def test_prints_current(self, tmp_versions_file, capsys):
        with patch.object(version_mod, "VERSIONS_FILE", tmp_versions_file):
            version_mod.cmd_current()
            captured = capsys.readouterr()
            assert "0.1.0" in captured.out
