"""Smoke: load the trained temporal model and run a dummy prediction."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

MODEL_PATH = Path(__file__).resolve().parents[2] / "data" / "results" / "models" / "temporal_model.joblib"


def test_model_loads_and_has_expected_features():
    if not MODEL_PATH.exists():
        pytest.skip(f"Model file not found: {MODEL_PATH}")

    import joblib

    model = joblib.load(MODEL_PATH)
    features = model.feature_names_in_
    assert len(features) == 25, f"Expected 25 features, got {len(features)}"


def test_model_predict_runs():
    if not MODEL_PATH.exists():
        pytest.skip(f"Model file not found: {MODEL_PATH}")

    import joblib

    model = joblib.load(MODEL_PATH)
    n_features = len(model.feature_names_in_)
    dummy_row = np.zeros((1, n_features))
    prediction = model.predict(dummy_row)
    assert prediction.shape == (1,), f"Unexpected prediction shape: {prediction.shape}"
