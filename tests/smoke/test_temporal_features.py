"""Smoke: verify _add_temporal_lags_and_target on a synthetic DataFrame."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.dataset_builder import FEATURE_COLUMNS
from src.models.temporal import _add_temporal_lags_and_target


def _make_synthetic_df(n_tiles: int = 3, n_months: int = 12) -> pd.DataFrame:
    """Build a minimal DataFrame that mirrors the real feature schema."""
    rng = np.random.default_rng(42)
    rows = []
    for tile in range(n_tiles):
        for month_offset in range(n_months):
            year = 2020 + month_offset // 12
            month = 1 + month_offset % 12
            row = {"tile_id": f"tile_{tile}", "year": year, "month": month}
            for col in FEATURE_COLUMNS:
                row[col] = rng.random()
            row["target_flood_risk"] = rng.random()
            rows.append(row)
    return pd.DataFrame(rows)


def test_no_nans_after_lag_transform():
    df = _make_synthetic_df()
    result = _add_temporal_lags_and_target(df)
    assert result.isna().sum().sum() == 0, "NaN values remain after lag transform"


def test_target_next_month_exists():
    df = _make_synthetic_df()
    result = _add_temporal_lags_and_target(df)
    assert "target_next_month" in result.columns, "target_next_month column missing"


def test_output_not_empty():
    df = _make_synthetic_df()
    result = _add_temporal_lags_and_target(df)
    assert len(result) > 0, "Lag transform returned empty DataFrame"
