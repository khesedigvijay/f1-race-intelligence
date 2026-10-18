"""
Unit tests for race strategy analysis and scenario simulations.
"""

import pytest
import pandas as pd
from data.sample_data import generate_sample_race_data
from analysis.race_strategy import extract_pit_stops, simulate_strategy_scenario

def test_extract_pit_stops():
    sample = generate_sample_race_data()
    laps = sample["laps"]
    pits = extract_pit_stops(laps)
    assert not pits.empty
    assert "Driver" in pits.columns
    assert "PitLap" in pits.columns

def test_simulate_strategy_scenario():
    sim = simulate_strategy_scenario(total_laps=50, pit_loss=22.0)
    assert "optimal_strategy" in sim
    assert len(sim["scenarios"]) >= 2
    for sc in sim["scenarios"]:
        assert sc["total_time_seconds"] > 0
        assert len(sc["cumulative_times"]) == 50
