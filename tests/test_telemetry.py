"""
Unit tests for telemetry analysis functions.
"""

import pytest
import pandas as pd
import numpy as np
from data.sample_data import generate_telemetry_profile
from analysis.telemetry import detect_braking_zones, detect_apexes, compute_telemetry_metrics
from utils.f1_data import synchronize_telemetry_by_distance

def test_telemetry_generation():
    df = generate_telemetry_profile("VER")
    assert not df.empty
    assert "Distance" in df.columns
    assert "Speed" in df.columns
    assert "Throttle" in df.columns
    assert "Brake" in df.columns
    assert df["Speed"].max() > 250.0

def test_braking_zones_detection():
    df = generate_telemetry_profile("VER")
    zones = detect_braking_zones(df)
    assert len(zones) >= 3
    for z in zones:
        assert z["LengthMeters"] > 0
        assert z["EntrySpeed"] >= z["MinSpeed"]

def test_apexes_detection():
    df = generate_telemetry_profile("VER")
    apexes = detect_apexes(df)
    assert len(apexes) >= 3
    for a in apexes:
        assert a["ApexSpeed"] < 220.0

def test_synchronize_telemetry():
    t1 = generate_telemetry_profile("VER", base_speed_delta=2.0)
    t2 = generate_telemetry_profile("LEC", base_speed_delta=0.0)
    
    s1, s2, delta = synchronize_telemetry_by_distance(t1, t2, num_points=500)
    assert len(s1) == 500
    assert len(s2) == 500
    assert len(delta) == 500
    assert "DeltaTime" in delta.columns
    assert "DeltaSpeed" in delta.columns
