"""
Tire degradation modeling and stint analytics.
Calculates compound-specific wear rates, fuel-corrected lap times,
stint comparisons, outlier lap identification, and statistical uncertainty.
"""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

def filter_clean_racing_laps(
    laps_df: pd.DataFrame, 
    filter_pit_laps: bool = True,
    filter_sc: bool = True,
    outlier_threshold_pct: float = 1.07
) -> pd.DataFrame:
    """
    Cleans laps dataframe by removing in/out laps, safety car / VSC laps, and extreme pace outliers.
    """
    if laps_df.empty or "LapTimeSeconds" not in laps_df.columns:
        return pd.DataFrame()

    df = laps_df.copy()
    df = df.dropna(subset=["LapTimeSeconds"])
    df = df[df["LapTimeSeconds"] > 50.0]  # Valid lap time floor

    # Filter pit laps
    if filter_pit_laps:
        if "IsPitIn" in df.columns:
            df = df[~df["IsPitIn"].fillna(False)]
        if "IsPitOut" in df.columns:
            df = df[~df["IsPitOut"].fillna(False)]
        if "PitInTime" in df.columns:
            df = df[df["PitInTime"].isna()]
        if "PitOutTime" in df.columns:
            df = df[df["PitOutTime"].isna()]

    # Filter Safety Car / VSC
    if filter_sc and "TrackStatus" in df.columns:
        # '1' is all-clear green flag track status
        df = df[df["TrackStatus"].astype(str).isin(["1", "12"])]

    # Outlier threshold based on median lap time per driver
    clean_records = []
    for driver, group in df.groupby("Driver"):
        median_time = group["LapTimeSeconds"].median()
        upper_limit = median_time * outlier_threshold_pct
        valid = group[group["LapTimeSeconds"] <= upper_limit]
        clean_records.append(valid)

    if clean_records:
        return pd.concat(clean_records, ignore_index=True)
    return df

def apply_fuel_correction(
    laps_df: pd.DataFrame, 
    fuel_effect_per_lap: float = 0.050, 
    total_laps: Optional[int] = None
) -> pd.DataFrame:
    """
    Applies empirical fuel-burn correction to isolate tire degradation from vehicle lightening.
    Lap time decreases by ~0.04-0.06s each lap as ~1.8kg fuel burns off.
    Fuel Corrected Lap Time = Raw Lap Time + (LapNumber * fuel_effect_per_lap)
    """
    if laps_df.empty or "LapTimeSeconds" not in laps_df.columns:
        return laps_df

    df = laps_df.copy()
    if "LapNumber" not in df.columns:
        return df

    # Adding fuel effect removes the artificial speedup from burning fuel
    df["FuelCorrectionSeconds"] = df["LapNumber"] * fuel_effect_per_lap
    df["CorrectedLapTimeSeconds"] = df["LapTimeSeconds"] + df["FuelCorrectionSeconds"]
    return df

def calculate_compound_degradation(
    laps_df: pd.DataFrame, 
    use_fuel_correction: bool = True,
    fuel_effect_per_lap: float = 0.050
) -> Dict[str, Any]:
    """
    Fits linear regression on Tire Age vs Lap Time for each compound to determine degradation slope (s/lap).
    Returns degradation rate, standard error, 95% confidence interval, and R-squared.
    """
    if laps_df.empty:
        return {}

    df = filter_clean_racing_laps(laps_df)
    if df.empty:
        return {}

    if use_fuel_correction:
        df = apply_fuel_correction(df, fuel_effect_per_lap)
        target_col = "CorrectedLapTimeSeconds"
    else:
        target_col = "LapTimeSeconds"

    if "TyreLife" not in df.columns:
        df["TyreLife"] = df.groupby(["Driver", "Stint"])["LapNumber"].rank().astype(int)

    results = {}
    compounds = df["Compound"].dropna().unique()

    for comp in compounds:
        sub = df[df["Compound"] == comp].dropna(subset=["TyreLife", target_col])
        if len(sub) < 5:
            continue

        x = sub["TyreLife"].values
        y = sub[target_col].values

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        n = len(x)
        # 95% confidence interval for slope: slope +/- t_crit * std_err
        t_crit = stats.t.ppf(0.975, df=max(1, n - 2))
        ci_lower = slope - t_crit * std_err
        ci_upper = slope + t_crit * std_err

        results[comp] = {
            "compound": comp,
            "sample_size": int(n),
            "degradation_rate_sec_per_lap": round(float(slope), 4),
            "base_pace_seconds": round(float(intercept), 3),
            "std_error": round(float(std_err), 4),
            "ci_95": (round(float(ci_lower), 4), round(float(ci_upper), 4)),
            "r_squared": round(float(r_value**2), 3),
            "p_value": round(float(p_value), 5),
            "data_points": sub[["TyreLife", target_col, "Driver", "LapNumber"]].to_dict(orient="records")
        }

    return results

def get_stint_breakdown(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes summary performance per stint for all drivers:
    Compound, start lap, end lap, stint length, mean pace, best pace, pace delta.
    """
    if laps_df.empty or "Stint" not in laps_df.columns:
        return pd.DataFrame()

    stint_rows = []
    clean = filter_clean_racing_laps(laps_df, filter_pit_laps=True, filter_sc=True)

    for (driver, stint), grp in clean.groupby(["Driver", "Stint"]):
        comp = grp["Compound"].iloc[0] if "Compound" in grp.columns else "UNKNOWN"
        start_lap = grp["LapNumber"].min()
        end_lap = grp["LapNumber"].max()
        laps_count = len(grp)
        mean_pace = grp["LapTimeSeconds"].mean()
        best_pace = grp["LapTimeSeconds"].min()
        
        # Pace loss from first 3 laps to last 3 laps of stint
        if laps_count >= 6:
            initial_pace = grp.iloc[:3]["LapTimeSeconds"].mean()
            final_pace = grp.iloc[-3:]["LapTimeSeconds"].mean()
            pace_loss = final_pace - initial_pace
        else:
            pace_loss = 0.0

        from utils.formatting import format_seconds_to_laptime

        stint_rows.append({
            "Driver": driver,
            "Stint": int(stint),
            "Compound": comp,
            "StartLap": int(start_lap),
            "EndLap": int(end_lap),
            "LapsCompleted": int(laps_count),
            "MeanLapTime": format_seconds_to_laptime(mean_pace),
            "BestLapTime": format_seconds_to_laptime(best_pace),
            "MeanSeconds": round(mean_pace, 3),
            "PaceLossSec": round(pace_loss, 3)
        })

    return pd.DataFrame(stint_rows).sort_values(["Driver", "Stint"])
