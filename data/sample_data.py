"""
Realistic synthetic Formula 1 data generator for offline/fallback/demo mode.
Provides high-fidelity mock data for Bahrain GP 2024 with realistic telemetry,
laps, stints, tire degradation, weather, and circuit coordinates.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

def generate_circuit_coordinates(n_points: int = 1000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates realistic 2D track coordinates (X, Y) resembling a modern GP circuit loop
    along with cumulative distance.
    """
    t = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    # Bahrain / generalized modern F1 circuit shape profile with straights, hairpins, and chicanes
    x = 1800 * np.cos(t) + 400 * np.cos(3 * t) - 250 * np.sin(2 * t)
    y = 900 * np.sin(t) + 450 * np.sin(2 * t) + 150 * np.cos(4 * t)
    
    # Calculate distance along the circuit
    dx = np.diff(x, append=x[0])
    dy = np.diff(y, append=y[0])
    step_dist = np.sqrt(dx**2 + dy**2)
    dist = np.cumsum(step_dist)
    total_len = dist[-1]
    # Scale to ~5412 meters (Bahrain standard length)
    scale = 5412.0 / total_len
    x = x * scale
    y = y * scale
    dist = dist * scale
    return x, y, dist

def generate_telemetry_profile(driver: str, base_speed_delta: float = 0.0) -> pd.DataFrame:
    """
    Generates detailed lap telemetry (Speed, Throttle, Brake, Gear, RPM, X, Y, Distance)
    for a single representative flying lap.
    """
    np.random.seed(42 if driver == "VER" else 99)
    x, y, dist = generate_circuit_coordinates(1100)
    n = len(dist)
    
    # Corners at approximate distances (m):
    # T1-T3 (600-900m), T4 (1500m), T8-T10 (2400-2800m), T11 (3300m), T14-T15 (4800-5100m)
    speed = np.zeros(n)
    throttle = np.zeros(n)
    brake = np.zeros(n)
    gear = np.zeros(n, dtype=int)
    rpm = np.zeros(n)

    for i, d in enumerate(dist):
        # Corner definitions
        in_t1 = (550 <= d <= 850)
        in_t4 = (1400 <= d <= 1650)
        in_t8_10 = (2350 <= d <= 2850)
        in_t11 = (3250 <= d <= 3500)
        in_t14 = (4750 <= d <= 5050)
        
        is_corner = in_t1 or in_t4 or in_t8_10 or in_t11 or in_t14
        
        if in_t1:
            target_speed = 78.0 + base_speed_delta
            th = 15.0 if d > 750 else 0.0
            br = 1.0 if d < 700 else 0.0
            g = 2 if d < 750 else 3
        elif in_t4:
            target_speed = 135.0 + base_speed_delta
            th = 30.0 if d > 1550 else 0.0
            br = 1.0 if d < 1520 else 0.0
            g = 4
        elif in_t8_10:
            target_speed = 88.0 + base_speed_delta
            th = 20.0 if d > 2700 else 0.0
            br = 1.0 if d < 2600 else 0.0
            g = 3
        elif in_t11:
            target_speed = 185.0 + base_speed_delta
            th = 60.0
            br = 0.0
            g = 5
        elif in_t14:
            target_speed = 115.0 + base_speed_delta
            th = 25.0 if d > 4950 else 0.0
            br = 1.0 if d < 4900 else 0.0
            g = 3
        else:
            # Straight / Acceleration zone
            # Main straight max speed up to 328 km/h
            if d < 550 or d > 5100:
                target_speed = 325.0 + base_speed_delta
                g = 8
            elif 1700 < d < 2300:
                target_speed = 295.0 + base_speed_delta
                g = 7
            elif 3600 < d < 4700:
                target_speed = 310.0 + base_speed_delta
                g = 8
            else:
                target_speed = 250.0 + base_speed_delta
                g = 6
            th = 100.0
            br = 0.0

        # Add minor natural telemetry noise
        noise = np.random.normal(0, 1.2)
        speed[i] = max(60.0, target_speed + noise)
        throttle[i] = max(0.0, min(100.0, th + np.random.normal(0, 1.5)))
        brake[i] = br
        gear[i] = g
        rpm[i] = int(8000 + (speed[i] / 330.0) * 4500 + np.random.randint(-100, 100))

    # Construct Time array assuming speed
    # dt = d_dist / (speed_m_s)
    speed_ms = np.maximum(speed * (1000.0 / 3600.0), 10.0)
    step_m = np.diff(dist, prepend=0)
    step_m[0] = step_m[1]
    time_delta = step_m / speed_ms
    cum_time = np.cumsum(time_delta)
    time_objs = pd.to_timedelta(cum_time, unit='s')

    df = pd.DataFrame({
        "Distance": dist,
        "Speed": np.round(speed, 1),
        "Throttle": np.round(throttle, 1),
        "Brake": brake,
        "nGear": gear,
        "RPM": rpm,
        "X": np.round(x, 1),
        "Y": np.round(y, 1),
        "Time": time_objs,
        "Driver": driver
    })
    return df

def generate_sample_race_data() -> Dict[str, Any]:
    """
    Generates a full synthetic suite representing 2024 Bahrain Grand Prix.
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

    # Detailed flying lap telemetry for VER and LEC
    tel_ver = generate_telemetry_profile("VER", base_speed_delta=2.5)
    tel_lec = generate_telemetry_profile("LEC", base_speed_delta=0.0)

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

    return {
        "event_name": "Bahrain Grand Prix",
        "official_name": "FORMULA 1 GULF AIR BAHRAIN GRAND PRIX 2024",
        "circuit_name": "Bahrain International Circuit",
        "country": "Bahrain",
        "location": "Sakhir",
        "season": 2024,
        "round": 1,
        "date": "2024-03-02",
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
