"""
FastAPI application — Audio Visualizer API.
"""

import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.routes import router
from app.cleanup import start_cleanup_scheduler

# ── Version file paths ───────────────────────────────────
_versions_file = Path(__file__).parent.parent / "versions.json"
_project_root = _versions_file.parent


def _load_version_data() -> dict:
    if _versions_file.exists():
        with open(_versions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"current": "0.0.0", "versions": []}


def _save_version_data(data: dict):
    with open(_versions_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # Copy to places Docker / static serving expects
    for dest_dir in [_versions_file.parent, _project_root / "frontend" / "public"]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "versions.json"
        if dest.resolve() != _versions_file.resolve():
            shutil.copy2(_versions_file, dest)


_version_data = _load_version_data()

app = FastAPI(
    title="Audio Visualizer API",
    version=_version_data.get("current", "0.1.0"),
    description="Create audio visualizers from YouTube URLs and download MP4",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup():
    start_cleanup_scheduler()


@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Version endpoints ────────────────────────────────────

class CreateVersionRequest(BaseModel):
    version: str
    description: str
    changes: List[str] = []


@app.get("/api/versions")
async def get_versions():
    """Return full version history."""
    return _load_version_data()


@app.post("/api/versions")
async def create_version(req: CreateVersionRequest):
    """Create a new version entry and persist it."""
    global _version_data

    data = _load_version_data()

    existing = [v["version"] for v in data.get("versions", [])]
    if req.version.strip() in existing:
        raise HTTPException(status_code=409, detail=f"Version {req.version} already exists")

    if not req.version.strip():
        raise HTTPException(status_code=422, detail="Version string cannot be empty")

    entry = {
        "version": req.version.strip(),
        "date": date.today().isoformat(),
        "description": req.description.strip(),
        "changes": [c.strip() for c in req.changes if c.strip()] or [req.description.strip()],
    }

    data.setdefault("versions", []).insert(0, entry)
    data["current"] = req.version.strip()

    _save_version_data(data)
    _version_data = data

    return data
