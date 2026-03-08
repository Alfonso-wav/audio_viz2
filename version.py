#!/usr/bin/env python3
"""
version.py — Audio Visualizer version management.

Usage:
  python version.py new <version> "<description>" ["change 1" "change 2" ...]
  python version.py list
  python version.py current

Examples:
  python version.py new 0.2.0 "Layer editor + presets" "New layer editor UI" "5 built-in presets" "Undo/redo support"
  python version.py list
  python version.py current
"""

import json
import sys
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
VERSIONS_FILE = ROOT / "versions.json"
BACKEND_MAIN = ROOT / "backend" / "app" / "main.py"
FRONTEND_PACKAGE = ROOT / "frontend" / "package.json"


def load_versions() -> dict:
    if not VERSIONS_FILE.exists():
        return {"current": "0.0.0", "versions": []}
    with open(VERSIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_versions(data: dict):
    with open(VERSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Updated {VERSIONS_FILE.name}")


def update_backend_version(version: str):
    """Update version string in FastAPI app."""
    if not BACKEND_MAIN.exists():
        print(f"  ⚠ {BACKEND_MAIN} not found, skipping")
        return

    content = BACKEND_MAIN.read_text(encoding="utf-8")
    import re
    new_content = re.sub(
        r'version="[^"]*"',
        f'version="{version}"',
        content,
        count=1,
    )
    BACKEND_MAIN.write_text(new_content, encoding="utf-8")
    print(f"  ✓ Updated backend version → {version}")


def update_frontend_version(version: str):
    """Update version in package.json."""
    if not FRONTEND_PACKAGE.exists():
        print(f"  ⚠ {FRONTEND_PACKAGE} not found, skipping")
        return

    with open(FRONTEND_PACKAGE, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    pkg["version"] = version

    with open(FRONTEND_PACKAGE, "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=2)
        f.write("\n")
    print(f"  ✓ Updated frontend version → {version}")


def copy_versions_to_services():
    """Copy versions.json into backend and frontend so Docker builds include it."""
    for dest_dir in [ROOT / "backend", ROOT / "frontend" / "public"]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "versions.json"
        shutil.copy2(VERSIONS_FILE, dest)
        print(f"  ✓ Copied to {dest.relative_to(ROOT)}")


def cmd_new(version: str, description: str, changes: list[str]):
    data = load_versions()

    # Check not duplicate
    existing = [v["version"] for v in data["versions"]]
    if version in existing:
        print(f"  ✗ Version {version} already exists!")
        sys.exit(1)

    entry = {
        "version": version,
        "date": date.today().isoformat(),
        "description": description,
        "changes": changes if changes else [description],
    }

    data["versions"].insert(0, entry)  # newest first
    data["current"] = version

    save_versions(data)
    update_backend_version(version)
    update_frontend_version(version)
    copy_versions_to_services()

    print(f"\n🎉 Version {version} saved!")
    print(f"   Now run: docker compose up --build")


def cmd_list():
    data = load_versions()
    current = data.get("current", "?")
    print(f"\nAudio Visualizer — versions (current: {current})\n")
    for v in data["versions"]:
        marker = " ← current" if v["version"] == current else ""
        print(f"  {v['version']}  ({v['date']}){marker}")
        print(f"    {v['description']}")
        for c in v.get("changes", []):
            print(f"      • {c}")
        print()


def cmd_current():
    data = load_versions()
    print(data.get("current", "0.0.0"))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "new":
        if len(sys.argv) < 4:
            print("Usage: python version.py new <version> <description> [changes...]")
            sys.exit(1)
        version = sys.argv[2]
        description = sys.argv[3]
        changes = sys.argv[4:] if len(sys.argv) > 4 else []
        cmd_new(version, description, changes)

    elif cmd == "list":
        cmd_list()

    elif cmd == "current":
        cmd_current()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
