"""
Race Strategy and Pit Stop Simulation Engine.
Analyzes pit sequences, detects undercut/overcut battles,
and simulates 1-stop vs 2-stop scenario outcomes with customizable parameters.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from utils.formatting import format_seconds_to_laptime

def extract_pit_stops(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts recorded pit stops per driver including lap, compound transition,
    and stint length.
    """
    if laps_df.empty or "LapNumber" not in laps_df.columns:
        return pd.DataFrame()

    pit_events = []
    
    for driver, group in laps_df.groupby("Driver"):
        sorted_laps = group.sort_values("LapNumber")
        for i in range(len(sorted_laps) - 1):
            curr_lap = sorted_laps.iloc[i]
            next_lap = sorted_laps.iloc[i + 1]
            
            # Check for pit stop indicators
            is_pit = False
            if "IsPitIn" in curr_lap and bool(curr_lap["IsPitIn"]):
                is_pit = True
            elif "PitInTime" in curr_lap and pd.notna(curr_lap["PitInTime"]):
                is_pit = True
            elif "Stint" in curr_lap and "Stint" in next_lap and curr_lap["Stint"] != next_lap["Stint"]:
                is_pit = True

            if is_pit:
                pit_events.append({
                    "Driver": driver,
                    "PitLap": int(curr_lap["LapNumber"]),
                    "FromCompound": str(curr_lap.get("Compound", "UNKNOWN")),
                    "ToCompound": str(next_lap.get("Compound", "UNKNOWN")),
                    "StintCompleted": int(curr_lap.get("Stint", 1)),
                    "TireAgeAtStop": int(curr_lap.get("TyreLife", curr_lap["LapNumber"])),
                    "LapTimeAtPit": format_seconds_to_laptime(curr_lap.get("LapTimeSeconds", np.nan))
                })

    return pd.DataFrame(pit_events).sort_values(["PitLap", "Driver"])

def evaluate_undercut_potential(laps_df: pd.DataFrame, pit_loss_seconds: float = 23.0) -> List[Dict[str, Any]]:
    """
    Analyzes undercut scenarios where an earlier pit stop enables a chasing driver
    to gain track position via fresh tire pace.
    """
    pits = extract_pit_stops(laps_df)
    if len(pits) < 2:
        return []

    insights = []
    drivers = laps_df["Driver"].unique()
    
    for i in range(len(drivers)):
        for j in range(i + 1, len(drivers)):
            d1 = drivers[i]
            d2 = drivers[j]
            
            p1 = pits[pits["Driver"] == d1]
            p2 = pits[pits["Driver"] == d2]
            
            if not p1.empty and not p2.empty:
                lap1 = p1.iloc[0]["PitLap"]
                lap2 = p2.iloc[0]["PitLap"]
                
                # Check for pit delta within 1-3 laps
                if 1 <= abs(lap1 - lap2) <= 3:
                    early_driver = d1 if lap1 < lap2 else d2
                    late_driver = d2 if lap1 < lap2 else d1
                    insights.append({
                        "attacker": early_driver,
                        "defender": late_driver,
                        "attacker_pit_lap": min(lap1, lap2),
                        "defender_pit_lap": max(lap1, lap2),
                        "lap_delta": abs(lap1 - lap2),
                        "type": "Undercut Window"
                    })

    return insights

def simulate_strategy_scenario(
    total_laps: int = 57,
    pit_loss: float = 23.0,
    base_hard_lap: float = 93.5,
    scenarios: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Simulates race progression and total race time for distinct strategy permutations.
    Returns lap-by-lap simulated lap times and cumulative race times.
    """
    # Compound speed offsets relative to Hard
    compound_offsets = {
        "SOFT": -0.85,    # Soft is ~0.85s faster fresh
        "MEDIUM": -0.45,  # Medium is ~0.45s faster fresh
        "HARD": 0.0       # Hard baseline
    }
    
    # Degradation rates (s/lap)
    deg_rates = {
        "SOFT": 0.088,
        "MEDIUM": 0.055,
        "HARD": 0.035
    }

    if scenarios is None:
        scenarios = [
            {
                "name": "1-Stop: Medium -> Hard",
                "stops": 1,
                "stints": [
                    {"compound": "MEDIUM", "laps": 25},
                    {"compound": "HARD", "laps": total_laps - 25}
                ]
            },
            {
                "name": "2-Stop: Soft -> Hard -> Soft",
                "stops": 2,
                "stints": [
                    {"compound": "SOFT", "laps": 16},
                    {"compound": "HARD", "laps": 22},
                    {"compound": "SOFT", "laps": total_laps - 38}
                ]
            },
            {
                "name": "2-Stop: Soft -> Hard -> Medium",
                "stops": 2,
                "stints": [
                    {"compound": "SOFT", "laps": 15},
                    {"compound": "HARD", "laps": 23},
                    {"compound": "MEDIUM", "laps": total_laps - 38}
                ]
            }
        ]

    simulation_results = []
    
    for sc in scenarios:
        current_lap = 1
        lap_times = []
        cumulative_times = []
        running_total = 0.0

        for s_idx, stint in enumerate(sc["stints"]):
            comp = stint["compound"]
            stint_len = stint["laps"]
            
            for s_lap in range(1, stint_len + 1):
                if current_lap > total_laps:
                    break

                # Fuel effect: car gets faster by 0.05s per lap as fuel burns off
                fuel_delta = -0.050 * (current_lap - 1)
                
                # Compound initial speed advantage
                comp_delta = compound_offsets.get(comp, 0.0)
                
                # Tire wear penalty
                wear = deg_rates.get(comp, 0.05) * (s_lap - 1)

                lap_sec = base_hard_lap + fuel_delta + comp_delta + wear

                # Add pit loss on in-lap (if not final stint)
                if s_lap == stint_len and s_idx < len(sc["stints"]) - 1:
                    lap_sec += pit_loss

                running_total += lap_sec
                lap_times.append(round(lap_sec, 3))
                cumulative_times.append(round(running_total, 3))
                current_lap += 1

        total_race_time = running_total
        minutes = int(total_race_time // 60)
        secs = total_race_time % 60
        formatted_total = f"{minutes}m {secs:05.2f}s"

        simulation_results.append({
            "name": sc["name"],
            "stops": sc["stops"],
            "total_time_seconds": round(total_race_time, 2),
            "formatted_total_time": formatted_total,
            "lap_times": lap_times,
            "cumulative_times": cumulative_times,
            "stints": sc["stints"]
        })

    # Sort scenarios by total simulated race time
    simulation_results.sort(key=lambda x: x["total_time_seconds"])
    fastest_time = simulation_results[0]["total_time_seconds"]

    for r in simulation_results:
        r["delta_to_optimal"] = round(r["total_time_seconds"] - fastest_time, 2)

    return {
        "optimal_strategy": simulation_results[0]["name"],
        "scenarios": simulation_results,
        "disclaimer": "Simulated estimates based on empirical degradation models; does not account for yellow flags or traffic."
    }
