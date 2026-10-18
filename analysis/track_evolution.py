"""
Track Evolution Analysis Module.
Examines session-by-session lap time progression (FP1 -> FP2 -> FP3 -> Q -> Race),
sector speed trends, and isolates rubbering-in from fuel/tire confounders.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

def compute_track_evolution_metrics(evolution_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes delta and percentage improvement across weekend sessions.
    """
    if evolution_df.empty or "BestLap" not in evolution_df.columns:
        return {}

    df = evolution_df.copy()
    first_session_lap = df.iloc[0]["BestLap"]
    quali_lap = None
    
    # Locate qualifying session or lowest lap
    q_rows = df[df["Session"].str.contains("Qualifying|Q3", case=False, na=False)]
    if not q_rows.empty:
        quali_lap = q_rows["BestLap"].min()
    else:
        quali_lap = df["BestLap"].min()

    total_track_gain = first_session_lap - quali_lap
    pct_gain = (total_track_gain / first_session_lap) * 100.0

    return {
        "initial_lap": round(float(first_session_lap), 3),
        "peak_quali_lap": round(float(quali_lap), 3),
        "total_evolution_seconds": round(float(total_track_gain), 3),
        "evolution_percentage": round(float(pct_gain), 2),
        "sessions_analyzed": len(df)
    }

def estimate_rubber_in_rate(laps_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Estimates within-session track evolution / rubbering-in rate.
    Analyzes lap time progression of comparable runs across lap count.
    """
    if laps_df.empty or "LapNumber" not in laps_df.columns or "LapTimeSeconds" not in laps_df.columns:
        return {"slope_sec_per_lap": 0.0, "status": "insufficient_data"}

    from analysis.tire_degradation import filter_clean_racing_laps
    clean = filter_clean_racing_laps(laps_df)
    if len(clean) < 10:
        return {"slope_sec_per_lap": 0.0, "status": "insufficient_data"}

    # Calculate average lap time across field for each lap number
    lap_averages = clean.groupby("LapNumber")["LapTimeSeconds"].median().reset_index()
    if len(lap_averages) < 5:
        return {"slope_sec_per_lap": 0.0, "status": "insufficient_data"}

    # Estimate field trend
    from scipy import stats
    slope, intercept, r_val, p_val, std_err = stats.linregress(lap_averages["LapNumber"], lap_averages["LapTimeSeconds"])

    return {
        "slope_sec_per_lap": round(float(slope), 4),
        "r_squared": round(float(r_val**2), 3),
        "p_value": round(float(p_val), 5),
        "status": "valid"
    }
