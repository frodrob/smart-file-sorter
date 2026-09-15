"""FastAPI application exposing the smart file sorter over HTTP.

The API operates entirely inside a server-managed *workspace* directory so the
web UI can safely generate demo files, preview a sort plan, and apply it without
touching anything else on disk.
"""

from __future__ import annotations

import os
import shutil

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import __version__
from .categories import category_for
from .sorter import build_plan, apply_plan

WORKSPACE = os.environ.get(
    "SFS_WORKSPACE", os.path.join(os.path.dirname(__file__), "..", "workspace_data")
)
WORKSPACE = os.path.abspath(WORKSPACE)

# A deliberately messy set of demo files spanning every category.
DEMO_FILES: dict[str, str] = {
    "vacation-beach.jpg": "fake image bytes",
    "profile-photo.png": "fake image bytes",
    "diagram.svg": "<svg></svg>",
    "resume.pdf": "fake pdf",
    "meeting-notes.md": "# Notes\n",
    "cover-letter.docx": "fake doc",
    "budget-2026.xlsx": "fake sheet",
    "contacts.csv": "name,email\n",
    "quarterly-review.pptx": "fake deck",
    "podcast-ep12.mp3": "fake audio",
    "demo-song.wav": "fake audio",
    "screen-recording.mp4": "fake video",
    "backup.zip": "fake archive",
    "logs.tar.gz": "fake archive",
    "main.py": "print('hello')\n",
    "app.tsx": "export default () => null\n",
    "config.yaml": "key: value\n",
    "database.sqlite": "fake db",
    "server.log": "INFO started\n",
    "mystery-file": "no extension here",
    "notes.unknownext": "who knows",
}


class ApplyRequest(BaseModel):
    dry_run: bool = False


def _ensure_workspace() -> None:
    os.makedirs(WORKSPACE, exist_ok=True)


def _list_state() -> dict:
    """Return the current workspace state: loose files plus organized folders."""
    _ensure_workspace()
    loose: list[dict] = []
    organized: dict[str, list[str]] = {}
    for name in sorted(os.listdir(WORKSPACE)):
        full = os.path.join(WORKSPACE, name)
        if os.path.isfile(full):
            loose.append(
                {
                    "name": name,
                    "category": category_for(name),
                    "size_bytes": os.path.getsize(full),
                }
            )
        elif os.path.isdir(full):
            organized[name] = sorted(os.listdir(full))
    return {"loose": loose, "organized": organized}


def create_app() -> FastAPI:
    app = FastAPI(title="Smart File Sorter", version=__version__)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__, "workspace": WORKSPACE}

    @app.get("/api/workspace")
    def workspace() -> dict:
        return _list_state()

    @app.post("/api/workspace/reset")
    def reset() -> dict:
        """Recreate a fresh, messy demo workspace."""
        if os.path.isdir(WORKSPACE):
            shutil.rmtree(WORKSPACE)
        _ensure_workspace()
        for name, content in DEMO_FILES.items():
            with open(os.path.join(WORKSPACE, name), "w", encoding="utf-8") as handle:
                handle.write(content)
        return _list_state()

    @app.post("/api/plan")
    def plan() -> dict:
        _ensure_workspace()
        return build_plan(WORKSPACE).to_dict()

    @app.post("/api/apply")
    def apply(request: ApplyRequest) -> dict:
        _ensure_workspace()
        current = build_plan(WORKSPACE)
        if current.total_files == 0:
            raise HTTPException(status_code=400, detail="No loose files to sort.")
        moves = apply_plan(WORKSPACE, current, dry_run=request.dry_run)
        return {"moves": moves, "state": _list_state()}

    return app


app = create_app()
