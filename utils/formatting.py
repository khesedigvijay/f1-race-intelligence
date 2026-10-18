"""
Formatting and styling utilities for Formula 1 Race Intelligence Dashboard.
Contains official/semi-official team colors, tire compound colors, and timing converters.
"""

from typing import Union
import pandas as pd
import numpy as np

# Official / Common F1 Team Colors (Hex)
TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "Red Bull": "#3671C6",
    "RBR": "#3671C6",
    "Ferrari": "#E80020",
    "FER": "#E80020",
    "Mercedes": "#27F4D2",
    "MER": "#27F4D2",
    "McLaren": "#FF8000",
    "MCL": "#FF8000",
    "Aston Martin": "#229971",
    "AMR": "#229971",
    "Alpine": "#0093CC",
    "ALP": "#0093CC",
    "Williams": "#64C4FF",
    "WIL": "#64C4FF",
    "RB": "#6692FF",
    "AlphaTauri": "#5E8FAA",
    "Kick Sauber": "#52E252",
    "Alfa Romeo": "#C92D4B",
    "Haas F1 Team": "#B6BABD",
    "Haas": "#B6BABD",
    "HAA": "#B6BABD",
}

DEFAULT_DRIVER_COLORS = [
    "#E10600", "#00D2BE", "#FF8000", "#3671C6", "#229971",
    "#C92D4B", "#64C4FF", "#52E252", "#E80020", "#FFF200",
    "#9B59B6", "#E67E22", "#1ABC9C", "#34495E", "#F39C12"
]

# Pirelli Tire Compound Standard Colors
COMPOUND_COLORS = {
    "SOFT": "#FF1801",
    "MEDIUM": "#FFF200",
    "HARD": "#FFFFFF",
    "INTERMEDIATE": "#39B54A",
    "WET": "#00A3E0",
    "UNKNOWN": "#888888",
    "TEST_UNKNOWN": "#888888"
}

def get_compound_color(compound: str) -> str:
    """Return hex color for a given tire compound."""
    if not isinstance(compound, str):
        return COMPOUND_COLORS["UNKNOWN"]
    c = compound.upper().strip()
    return COMPOUND_COLORS.get(c, COMPOUND_COLORS["UNKNOWN"])

def get_team_color(team_name: str, fallback_idx: int = 0) -> str:
    """Return hex color for team, or fallback."""
    if not isinstance(team_name, str):
        return DEFAULT_DRIVER_COLORS[fallback_idx % len(DEFAULT_DRIVER_COLORS)]
    for key, color in TEAM_COLORS.items():
        if key.lower() in team_name.lower():
            return color
    return DEFAULT_DRIVER_COLORS[fallback_idx % len(DEFAULT_DRIVER_COLORS)]

def format_seconds_to_laptime(seconds: Union[float, int, pd.Timedelta]) -> str:
    """
    Converts seconds or Timedelta to F1 standard format 'M:SS.mmm'.
    e.g., 89.432 -> '1:29.432'
    """
    if pd.isna(seconds) or seconds is None:
        return "N/A"
    
    if isinstance(seconds, pd.Timedelta):
        seconds = seconds.total_seconds()
        
    try:
        seconds = float(seconds)
        if seconds <= 0 or np.isnan(seconds) or np.isinf(seconds):
            return "N/A"
        minutes = int(seconds // 60)
        rem_seconds = seconds % 60
        return f"{minutes}:{rem_seconds:06.3f}"
    except (ValueError, TypeError):
        return "N/A"

def format_delta_time(delta_seconds: float) -> str:
    """
    Formats delta time with sign e.g., '+0.234' or '-0.120'.
    """
    if pd.isna(delta_seconds) or delta_seconds is None:
        return "N/A"
    try:
        val = float(delta_seconds)
        if np.isnan(val) or np.isinf(val):
            return "N/A"
        sign = "+" if val >= 0 else "-"
        return f"{sign}{abs(val):.3f}s"
    except (ValueError, TypeError):
        return "N/A"

def laptime_to_seconds(laptime_str: str) -> float:
    """
    Converts string 'M:SS.mmm' or 'SS.mmm' back to seconds float.
    """
    if not isinstance(laptime_str, str) or laptime_str == "N/A":
        return np.nan
    try:
        parts = laptime_str.strip().split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60.0 + float(parts[1])
        elif len(parts) == 1:
            return float(parts[0])
        return np.nan
    except Exception:
        return np.nan
