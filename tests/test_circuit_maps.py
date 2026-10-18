"""
Tests to verify authentic GPS coordinates and telemetry for all championship tracks.
"""
import pytest
from utils.f1_data import load_f1_session_data, get_driver_fastest_telemetry
from data.circuit_layouts import CIRCUIT_LAYOUTS, get_circuit_telemetry_df

def test_all_24_circuits_present():
    assert len(CIRCUIT_LAYOUTS) == 24
    for name, data in CIRCUIT_LAYOUTS.items():
        assert len(data["x"]) > 100, f"{name} should have > 100 coordinate points"
        assert len(data["y"]) == len(data["x"])
        assert len(data["distance"]) == len(data["x"])
        assert len(data["speed"]) == len(data["x"])

def test_authentic_track_geometry_not_fourier_loop():
    # Bahrain track length is ~5.4km
    bh = get_circuit_telemetry_df("Bahrain")
    assert 5000 <= bh["Distance"].max() <= 5700

    # Spa track length is ~7.0km
    spa = get_circuit_telemetry_df("Spa")
    assert 6800 <= spa["Distance"].max() <= 7200

    # Monaco track length is ~3.3km
    monaco = get_circuit_telemetry_df("Monaco")
    assert 3100 <= monaco["Distance"].max() <= 3500

def test_dynamic_grand_prix_telemetry():
    gps = [
        ("Bahrain Grand Prix", 5000, 5600),
        ("British Grand Prix", 5600, 6100),
        ("Monaco Grand Prix", 3100, 3500),
        ("Italian Grand Prix", 5500, 6000),
        ("Belgian Grand Prix", 6800, 7200),
        ("Japanese Grand Prix", 5600, 6000),
        ("United States Grand Prix", 5300, 5700),
        ("Sao Paulo Grand Prix", 4100, 4500)
    ]
    for gp, min_len, max_len in gps:
        data = load_f1_session_data(2024, gp, "Race", force_demo=True)
        assert data["event_name"] == gp
        tel = get_driver_fastest_telemetry(data, "VER")
        assert tel is not None
        assert not tel.empty
        assert min_len <= tel["Distance"].max() <= max_len, f"{gp} distance {tel['Distance'].max()} outside [{min_len}, {max_len}]"
