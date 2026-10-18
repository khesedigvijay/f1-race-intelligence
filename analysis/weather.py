"""
Weather analytics module.
Examines environmental conditions (Air & Track Temp, Humidity, Wind, Rain)
and performs statistical correlation against field lap times.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from scipy import stats

def summarize_weather(weather_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes mean, min, max, and trend for weather telemetry parameters.
    """
    if weather_df.empty:
        return {"available": False}

    df = weather_df.copy()
    
    def get_stats(col: str):
        if col in df.columns and not df[col].dropna().empty:
            s = df[col].astype(float)
            return {
                "mean": round(float(s.mean()), 1),
                "min": round(float(s.min()), 1),
                "max": round(float(s.max()), 1),
                "delta": round(float(s.iloc[-1] - s.iloc[0]), 1)
            }
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "delta": 0.0}

    rain_detected = False
    if "Rainfall" in df.columns:
        rain_detected = bool(df["Rainfall"].any())

    return {
        "available": True,
        "records_count": len(df),
        "air_temp": get_stats("AirTemp"),
        "track_temp": get_stats("TrackTemp"),
        "humidity": get_stats("Humidity"),
        "wind_speed": get_stats("WindSpeed"),
        "rainfall_present": rain_detected
    }

def correlate_weather_with_pace(weather_df: pd.DataFrame, laps_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Merges weather telemetry with lap times to compute Pearson correlation coefficients.
    Clearly notes correlation vs causation caveats.
    """
    if weather_df.empty or laps_df.empty or "TrackTemp" not in weather_df.columns:
        return {"correlation": 0.0, "p_value": 1.0, "note": "Insufficient weather telemetry"}

    from analysis.tire_degradation import filter_clean_racing_laps
    clean_laps = filter_clean_racing_laps(laps_df)
    if clean_laps.empty:
        return {"correlation": 0.0, "p_value": 1.0, "note": "Insufficient clean laps"}

    # Average lap time across field per lap
    avg_laps = clean_laps.groupby("LapNumber")["LapTimeSeconds"].mean().reset_index()

    # Interpolate track temp onto lap numbers
    n_laps = len(avg_laps)
    w_temps = weather_df["TrackTemp"].values
    if len(w_temps) < 2:
        return {"correlation": 0.0, "p_value": 1.0, "note": "Insufficient weather data points"}

    interpolated_temps = np.interp(
        np.linspace(0, len(w_temps) - 1, n_laps),
        np.arange(len(w_temps)),
        w_temps
    )

    r_val, p_val = stats.pearsonr(interpolated_temps, avg_laps["LapTimeSeconds"])

    return {
        "correlation": round(float(r_val), 3),
        "p_value": round(float(p_val), 4),
        "interpretation": "Negative correlation: pace improved as track cooled" if r_val < -0.3 else (
            "Positive correlation: pace slowed as track heated" if r_val > 0.3 else "Neutral / minimal linear relationship"
        ),
        "caveat": "Correlation does not imply causation. Fuel-burn, tire wear, and traffic occur simultaneously."
    }
