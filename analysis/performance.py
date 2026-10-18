"""
Driver and Team performance analytics:
- Race pace vs qualifying pace
- Sector dominance comparison
- Overtaking and position changes
- Consistency rankings
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from utils.formatting import format_seconds_to_laptime

def calculate_driver_pace_rankings(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Ranks drivers by representative race pace (median clean lap time)
    to eliminate outlier skews.
    """
    if laps_df.empty or "LapTimeSeconds" not in laps_df.columns:
        return pd.DataFrame()

    from analysis.tire_degradation import filter_clean_racing_laps
    clean = filter_clean_racing_laps(laps_df)
    if clean.empty:
        return pd.DataFrame()

    records = []
    best_overall_median = None

    grouped = clean.groupby("Driver")
    medians = grouped["LapTimeSeconds"].median().sort_values()

    if not medians.empty:
        best_overall_median = medians.iloc[0]

    for driver, median_sec in medians.items():
        sub = clean[clean["Driver"] == driver]
        fastest_sec = sub["LapTimeSeconds"].min()
        std_sec = sub["LapTimeSeconds"].std()
        laps_run = len(sub)
        
        delta_to_leader = median_sec - best_overall_median if best_overall_median else 0.0

        records.append({
            "Driver": driver,
            "LapsSampled": laps_run,
            "MedianPace": format_seconds_to_laptime(median_sec),
            "MedianSeconds": round(median_sec, 3),
            "BestLap": format_seconds_to_laptime(fastest_sec),
            "BestSeconds": round(fastest_sec, 3),
            "PaceDeltaToP1": f"+{delta_to_leader:.3f}s" if delta_to_leader > 0 else "0.000s",
            "DeltaSeconds": round(delta_to_leader, 3),
            "ConsistencyStdDev": round(float(std_sec) if not np.isnan(std_sec) else 0.0, 3)
        })

    return pd.DataFrame(records)

def calculate_sector_dominance(laps_df: pd.DataFrame, drivers: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Identifies best personal sector times for selected drivers.
    """
    if laps_df.empty:
        return pd.DataFrame()

    df = laps_df.copy()
    if drivers:
        df = df[df["Driver"].isin(drivers)]

    results = []
    for driver, grp in df.groupby("Driver"):
        s1 = grp["Sector1Seconds"].min() if "Sector1Seconds" in grp.columns else np.nan
        s2 = grp["Sector2Seconds"].min() if "Sector2Seconds" in grp.columns else np.nan
        s3 = grp["Sector3Seconds"].min() if "Sector3Seconds" in grp.columns else np.nan
        
        theoretical_best = (s1 + s2 + s3) if (pd.notna(s1) and pd.notna(s2) and pd.notna(s3)) else np.nan
        actual_best = grp["LapTimeSeconds"].min() if "LapTimeSeconds" in grp.columns else np.nan
        lap_loss = (actual_best - theoretical_best) if (pd.notna(actual_best) and pd.notna(theoretical_best)) else np.nan

        results.append({
            "Driver": driver,
            "BestS1": round(s1, 3) if pd.notna(s1) else 0.0,
            "BestS2": round(s2, 3) if pd.notna(s2) else 0.0,
            "BestS3": round(s3, 3) if pd.notna(s3) else 0.0,
            "TheoreticalLap": format_seconds_to_laptime(theoretical_best),
            "ActualBestLap": format_seconds_to_laptime(actual_best),
            "TheoreticalGain": f"{lap_loss:.3f}s" if pd.notna(lap_loss) else "N/A"
        })

    return pd.DataFrame(results)

def calculate_position_changes(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes net positions gained or lost from Grid to Finish.
    """
    if results_df.empty:
        return pd.DataFrame()

    df = results_df.copy()
    
    # Handle column names for Grid and Position
    grid_col = "grid" if "grid" in df.columns else ("GridPosition" if "GridPosition" in df.columns else None)
    pos_col = "pos" if "pos" in df.columns else ("Position" if "Position" in df.columns else None)
    driver_col = "code" if "code" in df.columns else ("Abbreviation" if "Abbreviation" in df.columns else "Driver")

    if not grid_col or not pos_col:
        return pd.DataFrame()

    df["Grid"] = pd.to_numeric(df[grid_col], errors="coerce").fillna(20).astype(int)
    df["Finish"] = pd.to_numeric(df[pos_col], errors="coerce").fillna(20).astype(int)
    df["DriverCode"] = df[driver_col].astype(str)
    df["PositionsGained"] = df["Grid"] - df["Finish"]

    return df[["DriverCode", "Grid", "Finish", "PositionsGained"]].sort_values("PositionsGained", ascending=False)
