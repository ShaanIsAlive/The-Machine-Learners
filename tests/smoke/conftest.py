# tests/smoke/conftest.py
"""Shared helpers for smoke tests."""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def project_root() -> Path:
    return PROJECT_ROOT
