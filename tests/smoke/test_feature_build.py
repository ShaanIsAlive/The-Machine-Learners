"""Smoke: verify the multi-city feature parquet has the expected schema."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

PARQUET_PATH = Path(__file__).resolve().parents[2] / "data" / "features" / "flood_dataset_multicity.parquet"

EXPECTED_COLUMNS = {"tile_id", "city", "year", "month", "target_flood_risk"}


def test_feature_parquet_columns():
    if not PARQUET_PATH.exists():
        pytest.skip(f"Dataset not found: {PARQUET_PATH}")

    df = pd.read_parquet(PARQUET_PATH)
    missing = EXPECTED_COLUMNS - set(df.columns)
    assert not missing, f"Missing columns: {missing}"


def test_feature_parquet_not_empty():
    if not PARQUET_PATH.exists():
        pytest.skip(f"Dataset not found: {PARQUET_PATH}")

    df = pd.read_parquet(PARQUET_PATH)
    assert len(df) > 0, "Feature parquet is empty"
