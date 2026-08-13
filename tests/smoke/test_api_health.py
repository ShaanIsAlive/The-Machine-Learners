"""Smoke: hit the FastAPI /metadata endpoint via TestClient."""
from __future__ import annotations

from pathlib import Path

import pytest

SCORES_PATH = Path(__file__).resolve().parents[2] / "data" / "results" / "vulnerability_scores.parquet"


def test_metadata_returns_200():
    if not SCORES_PATH.exists():
        pytest.skip(f"Scores file not found: {SCORES_PATH}")

    from fastapi.testclient import TestClient

    from src.api.app import app

    client = TestClient(app)
    response = client.get("/metadata")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def test_metadata_has_expected_keys():
    if not SCORES_PATH.exists():
        pytest.skip(f"Scores file not found: {SCORES_PATH}")

    from fastapi.testclient import TestClient

    from src.api.app import app

    client = TestClient(app)
    data = client.get("/metadata").json()
    assert "rows" in data, "'rows' key missing from /metadata response"
    assert "months" in data, "'months' key missing from /metadata response"
    assert "sources" in data, "'sources' key missing from /metadata response"
