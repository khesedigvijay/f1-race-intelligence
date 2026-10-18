"""
Unit tests for formatting utilities.
"""

import pytest
import pandas as pd
import numpy as np
from utils.formatting import (
    format_seconds_to_laptime,
    format_delta_time,
    laptime_to_seconds,
    get_compound_color,
    get_team_color
)

def test_format_seconds_to_laptime():
    assert format_seconds_to_laptime(90.123) == "1:30.123"
    assert format_seconds_to_laptime(59.999) == "0:59.999"
    assert format_seconds_to_laptime(pd.Timedelta(92.5, unit='s')) == "1:32.500"
    assert format_seconds_to_laptime(None) == "N/A"
    assert format_seconds_to_laptime(-5.0) == "N/A"

def test_format_delta_time():
    assert format_delta_time(0.25) == "+0.250s"
    assert format_delta_time(-0.12) == "-0.120s"
    assert format_delta_time(None) == "N/A"

def test_laptime_to_seconds():
    assert pytest.approx(laptime_to_seconds("1:30.500")) == 90.500
    assert pytest.approx(laptime_to_seconds("58.200")) == 58.200
    assert np.isnan(laptime_to_seconds("invalid"))

def test_colors():
    assert get_compound_color("SOFT") == "#FF1801"
    assert get_compound_color("MEDIUM") == "#FFF200"
    assert get_compound_color("HARD") == "#FFFFFF"
    assert get_team_color("Red Bull") == "#3671C6"
    assert get_team_color("Ferrari") == "#E80020"
