"""
Telemetry processing and analytics module:
- Distance-based telemetry alignment
- Corner apex, braking point, and acceleration zone detection
- Throttle & brake profile analysis
- Speed delta computation
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

def detect_braking_zones(tel_df: pd.DataFrame, min_brake_threshold: float = 0.5) -> List[Dict[str, Any]]:
    """
    Identifies discrete braking events along the lap from telemetry distance.
    Returns list of braking zones with start distance, end distance, entry speed, min speed, and delta.
    """
    if "Brake" not in tel_df.columns or "Distance" not in tel_df.columns or "Speed" not in tel_df.columns:
        return []

    braking_zones = []
    in_braking = False
    start_idx = 0
    
    brake_vals = tel_df["Brake"].values
    speed_vals = tel_df["Speed"].values
    dist_vals = tel_df["Distance"].values
    
    for i in range(len(brake_vals)):
        is_braking = brake_vals[i] >= min_brake_threshold
        if is_braking and not in_braking:
            in_braking = True
            start_idx = i
        elif not is_braking and in_braking:
            in_braking = False
            end_idx = i
            zone_dist = dist_vals[end_idx] - dist_vals[start_idx]
            if zone_dist >= 15.0:  # filter noise
                entry_speed = speed_vals[start_idx]
                min_speed = np.min(speed_vals[start_idx:end_idx+1])
                speed_dropped = entry_speed - min_speed
                braking_zones.append({
                    "Zone": len(braking_zones) + 1,
                    "StartDist": round(float(dist_vals[start_idx]), 1),
                    "EndDist": round(float(dist_vals[end_idx]), 1),
                    "LengthMeters": round(float(zone_dist), 1),
                    "EntrySpeed": round(float(entry_speed), 1),
                    "MinSpeed": round(float(min_speed), 1),
                    "SpeedDelta": round(float(speed_dropped), 1)
                })
    return braking_zones

def detect_apexes(tel_df: pd.DataFrame, window_size: int = 15) -> List[Dict[str, Any]]:
    """
    Detects local speed minima (corner apexes) along the lap distance.
    """
    if "Speed" not in tel_df.columns or "Distance" not in tel_df.columns:
        return []

    speed = tel_df["Speed"].values
    dist = tel_df["Distance"].values
    gear = tel_df["nGear"].values if "nGear" in tel_df.columns else np.zeros(len(speed))
    
    apexes = []
    # Simple rolling local minimum detector
    for i in range(window_size, len(speed) - window_size):
        if speed[i] < 200.0: # Corners typically below 200 km/h
            if speed[i] == np.min(speed[i - window_size : i + window_size + 1]):
                # Check distance from last detected apex to avoid duplicates
                if not apexes or (dist[i] - apexes[-1]["Distance"]) > 80.0:
                    apexes.append({
                        "Corner": len(apexes) + 1,
                        "Distance": round(float(dist[i]), 1),
                        "ApexSpeed": round(float(speed[i]), 1),
                        "Gear": int(gear[i]) if gear[i] > 0 else 3
                    })
    return apexes

def compute_telemetry_metrics(tel1: pd.DataFrame, tel2: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates summary comparison statistics between two synchronized telemetry streams.
    """
    s1_mean = float(tel1["Speed"].mean()) if "Speed" in tel1.columns else 0.0
    s2_mean = float(tel2["Speed"].mean()) if "Speed" in tel2.columns else 0.0
    s1_max = float(tel1["Speed"].max()) if "Speed" in tel1.columns else 0.0
    s2_max = float(tel2["Speed"].max()) if "Speed" in tel2.columns else 0.0
    
    th1_full = float((tel1["Throttle"] > 95.0).mean() * 100.0) if "Throttle" in tel1.columns else 0.0
    th2_full = float((tel2["Throttle"] > 95.0).mean() * 100.0) if "Throttle" in tel2.columns else 0.0
    
    br1_time = float((tel1["Brake"] > 0.1).mean() * 100.0) if "Brake" in tel1.columns else 0.0
    br2_time = float((tel2["Brake"] > 0.1).mean() * 100.0) if "Brake" in tel2.columns else 0.0

    return {
        "d1_mean_speed": round(s1_mean, 1),
        "d2_mean_speed": round(s2_mean, 1),
        "d1_top_speed": round(s1_max, 1),
        "d2_top_speed": round(s2_max, 1),
        "d1_full_throttle_pct": round(th1_full, 1),
        "d2_full_throttle_pct": round(th2_full, 1),
        "d1_braking_pct": round(br1_time, 1),
        "d2_braking_pct": round(br2_time, 1),
    }
