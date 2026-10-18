"""
Lap consistency scoring and outlier detection engine.
Uses statistical dispersion (Coefficient of Variation, IQR) and Isolation Forest / Z-scores
to evaluate driver pace repeatability and detect incident laps.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from analysis.tire_degradation import filter_clean_racing_laps

def compute_driver_consistency(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes consistency scores (0-100) for all drivers based on lap-time variability.
    Score = 100 * exp(-1.5 * CV) where CV is Coefficient of Variation of clean laps.
    """
    if laps_df.empty or "LapTimeSeconds" not in laps_df.columns:
        return pd.DataFrame()

    clean = filter_clean_racing_laps(laps_df)
    if clean.empty:
        return pd.DataFrame()

    results = []
    
    for driver, group in clean.groupby("Driver"):
        times = group["LapTimeSeconds"].values
        if len(times) < 5:
            continue

        mean_pace = np.mean(times)
        std_pace = np.std(times, ddof=1)
        q75, q25 = np.percentile(times, [75, 25])
        iqr = q75 - q25
        cv_pct = (std_pace / mean_pace) * 100.0  # Coefficient of Variation

        # Consistency score (higher is more consistent, capped at 100)
        # CV in F1 is typically between 0.3% and 1.8% in clean air
        score = max(10.0, min(99.5, 100.0 - (cv_pct * 35.0)))

        results.append({
            "Driver": driver,
            "CleanLaps": len(times),
            "ConsistencyScore": round(score, 1),
            "MeanLapSec": round(mean_pace, 3),
            "StdDevSec": round(std_pace, 3),
            "IQR_Sec": round(iqr, 3),
            "CV_Pct": round(cv_pct, 2),
            "Rating": "Robotic" if score >= 85 else ("Very High" if score >= 75 else ("Moderate" if score >= 60 else "Variable"))
        })

    return pd.DataFrame(results).sort_values("ConsistencyScore", ascending=False)

def detect_pace_outliers(driver_laps: pd.DataFrame, z_threshold: float = 2.2) -> pd.DataFrame:
    """
    Detects outlier laps for a driver using Z-score and median absolute deviation (MAD).
    Identifies anomalous pace changes caused by mistakes, traffic, or incidents.
    """
    if driver_laps.empty or "LapTimeSeconds" not in driver_laps.columns:
        return pd.DataFrame()

    df = driver_laps.copy().dropna(subset=["LapTimeSeconds"])
    med = df["LapTimeSeconds"].median()
    mad = np.median(np.abs(df["LapTimeSeconds"] - med))
    mad = max(mad, 0.05)  # avoid division by zero

    # Modified Z-score (robust against extreme outliers)
    df["ModifiedZScore"] = 0.6745 * (df["LapTimeSeconds"] - med) / mad
    df["IsOutlier"] = np.abs(df["ModifiedZScore"]) > z_threshold
    
    return df[df["IsOutlier"]][["LapNumber", "LapTimeSeconds", "ModifiedZScore", "Compound", "Stint"]]
