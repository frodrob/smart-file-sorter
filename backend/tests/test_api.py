import importlib
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SFS_WORKSPACE", str(tmp_path / "ws"))
    import smart_file_sorter.api as api

    importlib.reload(api)
    return TestClient(api.create_app())


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_reset_creates_demo_files(client):
    resp = client.post("/api/workspace/reset")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["loose"]) > 0
    assert body["organized"] == {}
    names = {f["name"] for f in body["loose"]}
    assert "resume.pdf" in names


def test_plan_then_apply_full_flow(client):
    client.post("/api/workspace/reset")

    plan = client.post("/api/plan").json()
    assert plan["total_files"] > 0
    assert "Images" in plan["groups"]

    applied = client.post("/api/apply", json={"dry_run": False}).json()
    assert len(applied["moves"]) == plan["total_files"]
    # After applying, no loose files remain and folders exist.
    assert applied["state"]["loose"] == []
    assert "Images" in applied["state"]["organized"]


def test_apply_with_no_files_errors(client):
    resp = client.post("/api/apply", json={"dry_run": False})
    assert resp.status_code == 400
