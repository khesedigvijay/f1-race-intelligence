"""
Unit tests for Machine Learning models and statistical consistency algorithms.
"""

import pytest
import numpy as np
import pandas as pd
from data.sample_data import generate_sample_race_data
from models.consistency_scorer import compute_driver_consistency, detect_pace_outliers
from models.degradation_model import fit_tire_wear_curve
from models.lap_time_predictor import train_time_aware_lap_predictor

def test_consistency_scorer():
    sample = generate_sample_race_data()
    laps = sample["laps"]
    cons = compute_driver_consistency(laps)
    assert not cons.empty
    assert "ConsistencyScore" in cons.columns
    for score in cons["ConsistencyScore"]:
        assert 0 <= score <= 100

def test_outlier_detection():
    sample = generate_sample_race_data()
    laps = sample["laps"]
    ver_laps = laps[laps["Driver"] == "VER"]
    outliers = detect_pace_outliers(ver_laps)
    assert isinstance(outliers, pd.DataFrame)

def test_fit_tire_wear_curve():
    ages = np.arange(1, 25)
    times = 90.0 + 0.08 * ages + np.random.normal(0, 0.05, len(ages))
    res = fit_tire_wear_curve(ages, times, degree=1)
    assert res["status"] == "success"
    assert pytest.approx(res["slope_sec_per_lap"], abs=0.03) == 0.08
    assert len(res["projected_lap_times"]) == 35

def test_time_aware_lap_predictor():
    sample = generate_sample_race_data()
    laps = sample["laps"]
    res = train_time_aware_lap_predictor(laps, train_split_pct=0.65)
    assert res["status"] == "success"
    assert res["mae"] < 2.5
    assert len(res["feature_importances"]) > 0
