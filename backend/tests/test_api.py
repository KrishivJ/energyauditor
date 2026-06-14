"""API integration tests — full create→configure→run→fetch→delete cycle (brief §9 Phase 3).

Uses a temp DB + storage dir via env so it never touches dev data.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from tests.synth import build_dataset


@pytest.fixture(scope="module")
def client():
    # env points at an isolated temp DB/storage via tests/conftest.py
    from app.main import app

    with TestClient(app) as c:
        yield c


def _upload(client, n=21):
    files = [
        (
            "files",
            (
                fn,
                io.BytesIO(content),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )
        for fn, content in build_dataset()[:n]
    ]
    return client.post("/api/analyses", files=files)


def test_health(client):
    assert client.get("/api/health").json() == {"ok": True}


def test_reference_endpoints(client):
    ef = client.get("/api/reference/emission-factors").json()
    assert ef[0]["region"] == "India" and ef[0]["factor"] == 0.7117
    tf = client.get("/api/reference/tariffs").json()
    assert tf[0]["low"] == 11 and "bill" in tf[0]["note"].lower()


def test_full_cycle(client):
    up = _upload(client)
    assert up.status_code == 200, up.text
    body = up.json()
    aid = body["analysisId"]
    assert len(body["files"]) == 21

    # detection preview present per file
    assert all("value" in f["detectedCols"] for f in body["files"])

    # configure
    cfg = {
        "mode": "cv",
        "occupiedStartHour": 7,
        "occupiedEndHour": 18,
        "workingDays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "tariff": {"low": 11, "mid": 12, "high": 13, "currency": "INR", "unit": "per kWh"},
        "emissionFactorTco2PerMwh": 0.7117,
    }
    assert client.put(f"/api/analyses/{aid}/config", json=cfg).json()["ok"] is True

    # run
    run = client.post(f"/api/analyses/{aid}/run")
    assert run.status_code == 200, run.text
    results = run.json()["results"]
    assert results["totalKwh"]["low"] < results["totalKwh"]["mid"] < results["totalKwh"]["high"]
    assert len(results["solar"]) == 1
    assert 0 < results["unoccupiedShare"] < 1
    assert len(results["hourlyProfile"]["workingDays"]) == 24

    # listed
    lst = client.get("/api/analyses").json()
    assert any(a["id"] == aid and a["status"] == "complete" for a in lst)

    # reopened with persisted results
    detail = client.get(f"/api/analyses/{aid}").json()
    assert detail["results"]["totalKwh"]["mid"] == results["totalKwh"]["mid"]
    assert detail["config"]["tariff"]["mid"] == 12

    # deleted
    assert client.delete(f"/api/analyses/{aid}").json()["ok"] is True
    assert client.get(f"/api/analyses/{aid}").status_code == 404


def test_rejects_unsupported_file(client):
    files = [("files", ("notes.txt", io.BytesIO(b"hello"), "text/plain"))]
    r = client.post("/api/analyses", files=files)
    assert r.status_code == 400
