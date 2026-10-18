"""
Unit tests for tire degradation analytics and fuel-burn correction.
"""

import pytest
import pandas as pd
import numpy as np
from data.sample_data import generate_sample_race_data
from analysis.tire_degradation import (
    filter_clean_racing_laps,
    apply_fuel_correction,
    calculate_compound_degradation,
    get_stint_breakdown
)

def test_clean_racing_laps():
    sample = generate_sample_race_data()
    laps = sample["laps"]
    
    clean = filter_clean_racing_laps(laps)
    assert not clean.empty
    # Ensure pit laps are removed
    assert clean["IsPitIn"].sum() == 0
    assert clean["IsPitOut"].sum() == 0

def test_fuel_correction():
    sample = generate_sample_race_data()
    laps = sample["laps"]
    corrected = apply_fuel_correction(laps, fuel_effect_per_lap=0.050)
    assert "CorrectedLapTimeSeconds" in corrected.columns
    # Check that lap 20 corrected time is larger than raw time by 20 * 0.05 = 1.0s
    sub = corrected[corrected["LapNumber"] == 20].iloc[0]
    assert pytest.approx(sub["CorrectedLapTimeSeconds"] - sub["LapTimeSeconds"]) == 1.0

def test_compound_degradation():
    sample = generate_sample_race_data()
    laps = sample["laps"]
    deg = calculate_compound_degradation(laps)
    assert "SOFT" in deg or "HARD" in deg
    for comp, s in deg.items():
        assert s["sample_size"] > 0
        assert "ci_95" in s
        assert "degradation_rate_sec_per_lap" in s

def test_stint_breakdown():
    sample = generate_sample_race_data()
    laps = sample["laps"]
    stints = get_stint_breakdown(laps)
    assert not stints.empty
    assert "MeanLapTime" in stints.columns
    assert "PaceLossSec" in stints.columns
