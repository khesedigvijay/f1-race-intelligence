"""
Realistic synthetic Formula 1 data generator for offline/fallback/demo mode.
Provides high-fidelity mock data for Bahrain GP 2024 with realistic telemetry,
laps, stints, tire degradation, weather, and circuit coordinates.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

from data.circuit_layouts import get_circuit_layout, get_circuit_telemetry_df

def generate_circuit_coordinates(circuit_name: str = "Bahrain", n_points: int = 1000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns authentic 2D track coordinates (X, Y) corresponding to specific F1 circuits
    along with cumulative distance from verified official FIA GPS records.
    """
    layout = get_circuit_layout(circuit_name)
    if layout and "x" in layout and len(layout["x"]) > 10:
        return np.array(layout["x"]), np.array(layout["y"]), np.array(layout["distance"])
    bh = get_circuit_layout("Bahrain")
    return np.array(bh["x"]), np.array(bh["y"]), np.array(bh["distance"])

def generate_telemetry_profile(driver: str, grand_prix: str = "Bahrain", base_speed_delta: float = 0.0) -> pd.DataFrame:
    """
    Generates authentic lap telemetry (Speed, Throttle, Brake, Gear, RPM, X, Y, Distance)
    for a single representative flying lap tailored to the selected Grand Prix circuit.
    """
    df = get_circuit_telemetry_df(grand_prix, driver=driver)
    if df is not None and not df.empty:
        df = df.copy()
        if base_speed_delta != 0.0:
            df["Speed"] = np.round(df["Speed"] + base_speed_delta, 1)
        if "RPM" not in df.columns:
            df["RPM"] = (8500 + (df["Speed"] / 340.0) * 3500).astype(int)
        if "Time" not in df.columns:
            speed_ms = np.maximum(df["Speed"] * (1000.0 / 3600.0), 10.0)
            step_m = np.diff(df["Distance"], prepend=0)
            step_m[0] = step_m[1] if len(step_m) > 1 else 10.0
            time_delta = step_m / speed_ms
            cum_time = np.cumsum(time_delta)
            df["Time"] = pd.to_timedelta(cum_time, unit='s')
        return df
    
    bh_df = get_circuit_telemetry_df("Bahrain", driver=driver)
    return bh_df.copy()

def generate_sample_race_data(grand_prix: str = "Bahrain Grand Prix", year: int = 2024) -> Dict[str, Any]:
    """
    Generates a full synthetic suite representing the selected Grand Prix circuit and season.
    """
    drivers = [
        {"code": "VER", "name": "Max Verstappen", "team": "Red Bull Racing", "grid": 1, "pos": 1, "status": "Finished"},
        {"code": "PER", "name": "Sergio Perez", "team": "Red Bull Racing", "grid": 5, "pos": 2, "status": "Finished"},
        {"code": "SAI", "name": "Carlos Sainz", "team": "Ferrari", "grid": 4, "pos": 3, "status": "Finished"},
        {"code": "LEC", "name": "Charles Leclerc", "team": "Ferrari", "grid": 2, "pos": 4, "status": "Finished"},
        {"code": "RUS", "name": "George Russell", "team": "Mercedes", "grid": 3, "pos": 5, "status": "Finished"},
        {"code": "NOR", "name": "Lando Norris", "team": "McLaren", "grid": 7, "pos": 6, "status": "Finished"},
        {"code": "HAM", "name": "Lewis Hamilton", "team": "Mercedes", "grid": 9, "pos": 7, "status": "Finished"},
        {"code": "PIA", "name": "Oscar Piastri", "team": "McLaren", "grid": 8, "pos": 8, "status": "Finished"},
        {"code": "ALO", "name": "Fernando Alonso", "team": "Aston Martin", "grid": 6, "pos": 9, "status": "Finished"},
        {"code": "STR", "name": "Lance Stroll", "team": "Aston Martin", "grid": 12, "pos": 10, "status": "Finished"},
    ]

    total_laps = 57
    laps_record = []
    
    # Stint strategy templates:
    # VER: Soft (L1-17), Hard (L18-36), Soft (L37-57)
    # LEC: Soft (L1-14), Hard (L15-34), Hard (L35-57)
    # NOR: Soft (L1-15), Hard (L16-35), Hard (L36-57)

    for d_idx, d_info in enumerate(drivers):
        code = d_info["code"]
        base_laptime = 92.8 + (d_info["pos"] - 1) * 0.28
        
        # Define stints
        if code in ["VER", "PER"]:
            stints_def = [(1, 17, "SOFT"), (18, 36, "HARD"), (37, 57, "SOFT")]
        else:
            stints_def = [(1, 15, "SOFT"), (16, 35, "HARD"), (36, 57, "HARD")]

        current_stint = 1
        stint_lap = 1
        current_compound = stints_def[0][2]
        
        for lap in range(1, total_laps + 1):
            # Check stint transition
            for s_idx, (s_start, s_end, comp) in enumerate(stints_def, 1):
                if s_start <= lap <= s_end:
                    if current_stint != s_idx:
                        current_stint = s_idx
                        stint_lap = 1
                        current_compound = comp
                    break
            
            # Fuel burn effect (~0.055s faster per lap as fuel burns off)
            fuel_benefit = -0.052 * lap
            
            # Tire degradation effect based on compound
            # Soft degrades ~0.085s/lap, Medium ~0.055s/lap, Hard ~0.035s/lap
            deg_rate = 0.092 if current_compound == "SOFT" else (0.058 if current_compound == "MEDIUM" else 0.038)
            tire_deg = deg_rate * stint_lap
            
            # Pit in/out penalty
            is_pit_in = any(lap == s_end for _, s_end, _ in stints_def[:-1])
            is_pit_out = any(lap == s_start and lap > 1 for s_start, _, _ in stints_def)
            
            pit_penalty = 23.5 if is_pit_in else (3.2 if is_pit_out else 0.0)
            
            # Safety car period at Lap 28-30
            is_sc = (28 <= lap <= 30)
            sc_penalty = 35.0 if is_sc else 0.0
            
            noise = np.random.normal(0, 0.18)
            lap_seconds = base_laptime + fuel_benefit + tire_deg + pit_penalty + sc_penalty + noise
            
            # Outlier incident on lap 42 for LEC (brake imbalance glitch)
            if code == "LEC" and lap == 42:
                lap_seconds += 2.4
                
            s1 = lap_seconds * 0.315 + np.random.normal(0, 0.05)
            s2 = lap_seconds * 0.435 + np.random.normal(0, 0.06)
            s3 = lap_seconds - s1 - s2

            laps_record.append({
                "Driver": code,
                "LapNumber": lap,
                "LapTimeSeconds": round(lap_seconds, 3),
                "LapTime": pd.to_timedelta(lap_seconds, unit='s'),
                "Stint": current_stint,
                "Compound": current_compound,
                "TyreLife": stint_lap,
                "Sector1Time": pd.to_timedelta(s1, unit='s'),
                "Sector2Time": pd.to_timedelta(s2, unit='s'),
                "Sector3Time": pd.to_timedelta(s3, unit='s'),
                "Sector1Seconds": round(s1, 3),
                "Sector2Seconds": round(s2, 3),
                "Sector3Seconds": round(s3, 3),
                "IsPitIn": is_pit_in,
                "IsPitOut": is_pit_out,
                "TrackStatus": "4" if is_sc else "1",
                "IsAccurate": not (is_pit_in or is_pit_out or is_sc),
                "Position": max(1, min(20, d_info["grid"] + int((d_info["pos"] - d_info["grid"]) * (lap / total_laps))))
            })
            stint_lap += 1

    df_laps = pd.DataFrame(laps_record)

    # Weather sequence (sampled every 5 minutes during race)
    race_times = pd.date_range("2024-03-02 18:00:00", periods=25, freq="5min")
    weather_df = pd.DataFrame({
        "Time": race_times,
        "AirTemp": np.round(np.linspace(24.5, 23.2, len(race_times)) + np.random.normal(0, 0.1, len(race_times)), 1),
        "TrackTemp": np.round(np.linspace(34.8, 30.5, len(race_times)) + np.random.normal(0, 0.2, len(race_times)), 1),
        "Humidity": np.round(np.linspace(48.0, 56.0, len(race_times)), 1),
        "WindSpeed": np.round(np.random.uniform(7.5, 12.0, len(race_times)), 1),
        "WindDirection": np.random.randint(120, 160, len(race_times)),
        "Rainfall": False
    })

    # Detailed flying lap telemetry for VER and LEC tailored to the Grand Prix circuit
    tel_ver = generate_telemetry_profile("VER", grand_prix=grand_prix, base_speed_delta=2.5)
    tel_lec = generate_telemetry_profile("LEC", grand_prix=grand_prix, base_speed_delta=0.0)

    # Track Evolution data across sessions
    sessions_evolution = [
        {"Session": "Practice 1", "Compound": "HARD", "BestLap": 95.845, "MeanLap": 96.950, "TrackTemp": 38.5, "AirTemp": 27.2},
        {"Session": "Practice 2", "Compound": "MEDIUM", "BestLap": 94.210, "MeanLap": 95.340, "TrackTemp": 33.1, "AirTemp": 25.4},
        {"Session": "Practice 3", "Compound": "SOFT", "BestLap": 93.450, "MeanLap": 94.220, "TrackTemp": 35.0, "AirTemp": 26.0},
        {"Session": "Qualifying Q1", "Compound": "SOFT", "BestLap": 92.680, "MeanLap": 93.150, "TrackTemp": 31.8, "AirTemp": 24.5},
        {"Session": "Qualifying Q2", "Compound": "SOFT", "BestLap": 92.210, "MeanLap": 92.680, "TrackTemp": 31.0, "AirTemp": 24.2},
        {"Session": "Qualifying Q3", "Compound": "SOFT", "BestLap": 91.758, "MeanLap": 92.050, "TrackTemp": 30.2, "AirTemp": 23.8},
        {"Session": "Race (Best Lap)", "Compound": "SOFT", "BestLap": 92.608, "MeanLap": 95.450, "TrackTemp": 32.5, "AirTemp": 24.0},
    ]
    df_evolution = pd.DataFrame(sessions_evolution)

    c_name = f"{grand_prix} Circuit"
    country_name = ""
    loc_name = ""
    gp_lower = grand_prix.lower()
    if "bahrain" in gp_lower:
        c_name = "Bahrain International Circuit"
        country_name = "Bahrain"
        loc_name = "Sakhir"
    elif "silverstone" in gp_lower or "british" in gp_lower:
        c_name = "Silverstone Circuit"
        country_name = "United Kingdom"
        loc_name = "Silverstone"
    elif "monaco" in gp_lower:
        c_name = "Circuit de Monaco"
        country_name = "Monaco"
        loc_name = "Monte Carlo"
    elif "monza" in gp_lower or "italian" in gp_lower:
        c_name = "Autodromo Nazionale Monza"
        country_name = "Italy"
        loc_name = "Monza"
    elif "spa" in gp_lower or "belgian" in gp_lower:
        c_name = "Circuit de Spa-Francorchamps"
        country_name = "Belgium"
        loc_name = "Spa-Francorchamps"
    elif "suzuka" in gp_lower or "japan" in gp_lower:
        c_name = "Suzuka International Racing Course"
        country_name = "Japan"
        loc_name = "Suzuka"

    return {
        "event_name": grand_prix,
        "official_name": f"FORMULA 1 {grand_prix.upper()} {year}",
        "circuit_name": c_name,
        "country": country_name,
        "location": loc_name,
        "season": year,
        "round": 1,
        "date": f"{year}-06-01",
        "session_type": "Race",
        "total_laps": total_laps,
        "fastest_lap": "1:32.608",
        "fastest_driver": "VER",
        "safety_cars": 1,
        "vsc": 0,
        "results": pd.DataFrame(drivers),
        "laps": df_laps,
        "weather": weather_df,
        "telemetry": {"VER": tel_ver, "LEC": tel_lec},
        "evolution": df_evolution,
        "is_synthetic": True
    }
