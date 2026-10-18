"""
FastF1 and OpenF1 Dual-Engine Data Loader.
Features:
- FastF1 integration with disk caching
- OpenF1 automatic fallback for official live FIA timing & telemetry
- Distance-based telemetry alignment and synchronization
- Seamless offline synthetic demo fallback with clear integrity status
"""

import os
import re
import pickle
import logging
from typing import Dict, Any, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger("f1_race_intelligence")

# Setup cache directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "data", "fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Configure connection-pooled HTTP session for OpenF1
_openf1_session = requests.Session()
_retries = Retry(
    total=3,
    backoff_factor=0.6,
    status_forcelist=[429, 500, 502, 503, 504],
    raise_on_status=False
)
_adapter = HTTPAdapter(max_retries=_retries, pool_connections=15, pool_maxsize=15)
_openf1_session.mount("https://", _adapter)
_openf1_session.mount("http://", _adapter)
_openf1_session.headers.update({"User-Agent": "F1RaceIntelligenceDashboard/1.0"})

def _safe_openf1_query(endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 12) -> Optional[List[Dict[str, Any]]]:
    """
    Safely executes an OpenF1 API request and guarantees a list of dictionary records.
    Returns None if the endpoint fails, returns an error object, or is empty.
    """
    url = f"https://api.openf1.org/v1/{endpoint}"
    try:
        resp = _openf1_session.get(url, params=params, timeout=timeout)
        if resp.status_code != 200:
            logger.warning(f"OpenF1 {endpoint} returned status {resp.status_code}")
            return None
        data = resp.json()
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        elif isinstance(data, dict):
            if any(k in data for k in ("detail", "message", "error")):
                logger.warning(f"OpenF1 {endpoint} returned error payload: {data}")
                return None
            return [data]
        return None
    except Exception as err:
        logger.warning(f"OpenF1 query failed ({url}): {err}")
        return None

# Attempt to configure FastF1
FASTF1_AVAILABLE = False
try:
    import fastf1
    fastf1.Cache.enable_cache(CACHE_DIR)
    FASTF1_AVAILABLE = True
except Exception as e:
    logger.warning(f"FastF1 could not enable cache or is not installed: {e}")

from data.sample_data import generate_sample_race_data, generate_telemetry_profile

def get_available_seasons() -> List[int]:
    """Returns list of selectable F1 seasons with complete high-resolution telemetry and GPS data."""
    return [2024, 2023, 2022, 2021, 2020]

OFFICIAL_CALENDARS: Dict[int, List[Dict[str, Any]]] = {
    2024: [
        {"RoundNumber": 1, "EventName": "Bahrain Grand Prix", "Country": "Bahrain", "Location": "Sakhir", "EventFormat": "conventional"},
        {"RoundNumber": 2, "EventName": "Saudi Arabian Grand Prix", "Country": "Saudi Arabia", "Location": "Jeddah", "EventFormat": "conventional"},
        {"RoundNumber": 3, "EventName": "Australian Grand Prix", "Country": "Australia", "Location": "Melbourne", "EventFormat": "conventional"},
        {"RoundNumber": 4, "EventName": "Japanese Grand Prix", "Country": "Japan", "Location": "Suzuka", "EventFormat": "conventional"},
        {"RoundNumber": 5, "EventName": "Chinese Grand Prix", "Country": "China", "Location": "Shanghai", "EventFormat": "sprint"},
        {"RoundNumber": 6, "EventName": "Miami Grand Prix", "Country": "USA", "Location": "Miami", "EventFormat": "sprint"},
        {"RoundNumber": 7, "EventName": "Emilia Romagna Grand Prix", "Country": "Italy", "Location": "Imola", "EventFormat": "conventional"},
        {"RoundNumber": 8, "EventName": "Monaco Grand Prix", "Country": "Monaco", "Location": "Monte Carlo", "EventFormat": "conventional"},
        {"RoundNumber": 9, "EventName": "Canadian Grand Prix", "Country": "Canada", "Location": "Montreal", "EventFormat": "conventional"},
        {"RoundNumber": 10, "EventName": "Spanish Grand Prix", "Country": "Spain", "Location": "Barcelona", "EventFormat": "conventional"},
        {"RoundNumber": 11, "EventName": "Austrian Grand Prix", "Country": "Austria", "Location": "Spielberg", "EventFormat": "sprint"},
        {"RoundNumber": 12, "EventName": "British Grand Prix", "Country": "Great Britain", "Location": "Silverstone", "EventFormat": "conventional"},
        {"RoundNumber": 13, "EventName": "Hungarian Grand Prix", "Country": "Hungary", "Location": "Budapest", "EventFormat": "conventional"},
        {"RoundNumber": 14, "EventName": "Belgian Grand Prix", "Country": "Belgium", "Location": "Spa-Francorchamps", "EventFormat": "conventional"},
        {"RoundNumber": 15, "EventName": "Dutch Grand Prix", "Country": "Netherlands", "Location": "Zandvoort", "EventFormat": "conventional"},
        {"RoundNumber": 16, "EventName": "Italian Grand Prix", "Country": "Italy", "Location": "Monza", "EventFormat": "conventional"},
        {"RoundNumber": 17, "EventName": "Azerbaijan Grand Prix", "Country": "Azerbaijan", "Location": "Baku", "EventFormat": "conventional"},
        {"RoundNumber": 18, "EventName": "Singapore Grand Prix", "Country": "Singapore", "Location": "Marina Bay", "EventFormat": "conventional"},
        {"RoundNumber": 19, "EventName": "United States Grand Prix", "Country": "USA", "Location": "Austin", "EventFormat": "sprint"},
        {"RoundNumber": 20, "EventName": "Mexico City Grand Prix", "Country": "Mexico", "Location": "Mexico City", "EventFormat": "conventional"},
        {"RoundNumber": 21, "EventName": "Sao Paulo Grand Prix", "Country": "Brazil", "Location": "Interlagos", "EventFormat": "sprint"},
        {"RoundNumber": 22, "EventName": "Las Vegas Grand Prix", "Country": "USA", "Location": "Las Vegas", "EventFormat": "conventional"},
        {"RoundNumber": 23, "EventName": "Qatar Grand Prix", "Country": "Qatar", "Location": "Lusail", "EventFormat": "sprint"},
        {"RoundNumber": 24, "EventName": "Abu Dhabi Grand Prix", "Country": "UAE", "Location": "Yas Marina", "EventFormat": "conventional"},
    ],
    2023: [
        {"RoundNumber": 1, "EventName": "Bahrain Grand Prix", "Country": "Bahrain", "Location": "Sakhir", "EventFormat": "conventional"},
        {"RoundNumber": 2, "EventName": "Saudi Arabian Grand Prix", "Country": "Saudi Arabia", "Location": "Jeddah", "EventFormat": "conventional"},
        {"RoundNumber": 3, "EventName": "Australian Grand Prix", "Country": "Australia", "Location": "Melbourne", "EventFormat": "conventional"},
        {"RoundNumber": 4, "EventName": "Azerbaijan Grand Prix", "Country": "Azerbaijan", "Location": "Baku", "EventFormat": "sprint"},
        {"RoundNumber": 5, "EventName": "Miami Grand Prix", "Country": "USA", "Location": "Miami", "EventFormat": "conventional"},
        {"RoundNumber": 6, "EventName": "Monaco Grand Prix", "Country": "Monaco", "Location": "Monte Carlo", "EventFormat": "conventional"},
        {"RoundNumber": 7, "EventName": "Spanish Grand Prix", "Country": "Spain", "Location": "Barcelona", "EventFormat": "conventional"},
        {"RoundNumber": 8, "EventName": "Canadian Grand Prix", "Country": "Canada", "Location": "Montreal", "EventFormat": "conventional"},
        {"RoundNumber": 9, "EventName": "Austrian Grand Prix", "Country": "Austria", "Location": "Spielberg", "EventFormat": "sprint"},
        {"RoundNumber": 10, "EventName": "British Grand Prix", "Country": "Great Britain", "Location": "Silverstone", "EventFormat": "conventional"},
        {"RoundNumber": 11, "EventName": "Hungarian Grand Prix", "Country": "Hungary", "Location": "Budapest", "EventFormat": "conventional"},
        {"RoundNumber": 12, "EventName": "Belgian Grand Prix", "Country": "Belgium", "Location": "Spa-Francorchamps", "EventFormat": "sprint"},
        {"RoundNumber": 13, "EventName": "Dutch Grand Prix", "Country": "Netherlands", "Location": "Zandvoort", "EventFormat": "conventional"},
        {"RoundNumber": 14, "EventName": "Italian Grand Prix", "Country": "Italy", "Location": "Monza", "EventFormat": "conventional"},
        {"RoundNumber": 15, "EventName": "Singapore Grand Prix", "Country": "Singapore", "Location": "Marina Bay", "EventFormat": "conventional"},
        {"RoundNumber": 16, "EventName": "Japanese Grand Prix", "Country": "Japan", "Location": "Suzuka", "EventFormat": "conventional"},
        {"RoundNumber": 17, "EventName": "Qatar Grand Prix", "Country": "Qatar", "Location": "Lusail", "EventFormat": "sprint"},
        {"RoundNumber": 18, "EventName": "United States Grand Prix", "Country": "USA", "Location": "Austin", "EventFormat": "sprint"},
        {"RoundNumber": 19, "EventName": "Mexico City Grand Prix", "Country": "Mexico", "Location": "Mexico City", "EventFormat": "conventional"},
        {"RoundNumber": 20, "EventName": "Sao Paulo Grand Prix", "Country": "Brazil", "Location": "Interlagos", "EventFormat": "sprint"},
        {"RoundNumber": 21, "EventName": "Las Vegas Grand Prix", "Country": "USA", "Location": "Las Vegas", "EventFormat": "conventional"},
        {"RoundNumber": 22, "EventName": "Abu Dhabi Grand Prix", "Country": "UAE", "Location": "Yas Marina", "EventFormat": "conventional"},
    ],
    2022: [
        {"RoundNumber": 1, "EventName": "Bahrain Grand Prix", "Country": "Bahrain", "Location": "Sakhir", "EventFormat": "conventional"},
        {"RoundNumber": 2, "EventName": "Saudi Arabian Grand Prix", "Country": "Saudi Arabia", "Location": "Jeddah", "EventFormat": "conventional"},
        {"RoundNumber": 3, "EventName": "Australian Grand Prix", "Country": "Australia", "Location": "Melbourne", "EventFormat": "conventional"},
        {"RoundNumber": 4, "EventName": "Emilia Romagna Grand Prix", "Country": "Italy", "Location": "Imola", "EventFormat": "sprint"},
        {"RoundNumber": 5, "EventName": "Miami Grand Prix", "Country": "USA", "Location": "Miami", "EventFormat": "conventional"},
        {"RoundNumber": 6, "EventName": "Spanish Grand Prix", "Country": "Spain", "Location": "Barcelona", "EventFormat": "conventional"},
        {"RoundNumber": 7, "EventName": "Monaco Grand Prix", "Country": "Monaco", "Location": "Monte Carlo", "EventFormat": "conventional"},
        {"RoundNumber": 8, "EventName": "Azerbaijan Grand Prix", "Country": "Azerbaijan", "Location": "Baku", "EventFormat": "conventional"},
        {"RoundNumber": 9, "EventName": "Canadian Grand Prix", "Country": "Canada", "Location": "Montreal", "EventFormat": "conventional"},
        {"RoundNumber": 10, "EventName": "British Grand Prix", "Country": "Great Britain", "Location": "Silverstone", "EventFormat": "conventional"},
        {"RoundNumber": 11, "EventName": "Austrian Grand Prix", "Country": "Austria", "Location": "Spielberg", "EventFormat": "sprint"},
        {"RoundNumber": 12, "EventName": "French Grand Prix", "Country": "France", "Location": "Le Castellet", "EventFormat": "conventional"},
        {"RoundNumber": 13, "EventName": "Hungarian Grand Prix", "Country": "Hungary", "Location": "Budapest", "EventFormat": "conventional"},
        {"RoundNumber": 14, "EventName": "Belgian Grand Prix", "Country": "Belgium", "Location": "Spa-Francorchamps", "EventFormat": "conventional"},
        {"RoundNumber": 15, "EventName": "Dutch Grand Prix", "Country": "Netherlands", "Location": "Zandvoort", "EventFormat": "conventional"},
        {"RoundNumber": 16, "EventName": "Italian Grand Prix", "Country": "Italy", "Location": "Monza", "EventFormat": "conventional"},
        {"RoundNumber": 17, "EventName": "Singapore Grand Prix", "Country": "Singapore", "Location": "Marina Bay", "EventFormat": "conventional"},
        {"RoundNumber": 18, "EventName": "Japanese Grand Prix", "Country": "Japan", "Location": "Suzuka", "EventFormat": "conventional"},
        {"RoundNumber": 19, "EventName": "United States Grand Prix", "Country": "USA", "Location": "Austin", "EventFormat": "conventional"},
        {"RoundNumber": 20, "EventName": "Mexico City Grand Prix", "Country": "Mexico", "Location": "Mexico City", "EventFormat": "conventional"},
        {"RoundNumber": 21, "EventName": "Sao Paulo Grand Prix", "Country": "Brazil", "Location": "Interlagos", "EventFormat": "sprint"},
        {"RoundNumber": 22, "EventName": "Abu Dhabi Grand Prix", "Country": "UAE", "Location": "Yas Marina", "EventFormat": "conventional"},
    ],
    2021: [
        {"RoundNumber": 1, "EventName": "Bahrain Grand Prix", "Country": "Bahrain", "Location": "Sakhir", "EventFormat": "conventional"},
        {"RoundNumber": 2, "EventName": "Emilia Romagna Grand Prix", "Country": "Italy", "Location": "Imola", "EventFormat": "conventional"},
        {"RoundNumber": 3, "EventName": "Portuguese Grand Prix", "Country": "Portugal", "Location": "Portimão", "EventFormat": "conventional"},
        {"RoundNumber": 4, "EventName": "Spanish Grand Prix", "Country": "Spain", "Location": "Barcelona", "EventFormat": "conventional"},
        {"RoundNumber": 5, "EventName": "Monaco Grand Prix", "Country": "Monaco", "Location": "Monte Carlo", "EventFormat": "conventional"},
        {"RoundNumber": 6, "EventName": "Azerbaijan Grand Prix", "Country": "Azerbaijan", "Location": "Baku", "EventFormat": "conventional"},
        {"RoundNumber": 7, "EventName": "French Grand Prix", "Country": "France", "Location": "Le Castellet", "EventFormat": "conventional"},
        {"RoundNumber": 8, "EventName": "Styrian Grand Prix", "Country": "Austria", "Location": "Spielberg", "EventFormat": "conventional"},
        {"RoundNumber": 9, "EventName": "Austrian Grand Prix", "Country": "Austria", "Location": "Spielberg", "EventFormat": "conventional"},
        {"RoundNumber": 10, "EventName": "British Grand Prix", "Country": "Great Britain", "Location": "Silverstone", "EventFormat": "sprint"},
        {"RoundNumber": 11, "EventName": "Hungarian Grand Prix", "Country": "Hungary", "Location": "Budapest", "EventFormat": "conventional"},
        {"RoundNumber": 12, "EventName": "Belgian Grand Prix", "Country": "Belgium", "Location": "Spa-Francorchamps", "EventFormat": "conventional"},
        {"RoundNumber": 13, "EventName": "Dutch Grand Prix", "Country": "Netherlands", "Location": "Zandvoort", "EventFormat": "conventional"},
        {"RoundNumber": 14, "EventName": "Italian Grand Prix", "Country": "Italy", "Location": "Monza", "EventFormat": "sprint"},
        {"RoundNumber": 15, "EventName": "Russian Grand Prix", "Country": "Russia", "Location": "Sochi", "EventFormat": "conventional"},
        {"RoundNumber": 16, "EventName": "Turkish Grand Prix", "Country": "Turkey", "Location": "Istanbul", "EventFormat": "conventional"},
        {"RoundNumber": 17, "EventName": "United States Grand Prix", "Country": "USA", "Location": "Austin", "EventFormat": "conventional"},
        {"RoundNumber": 18, "EventName": "Mexico City Grand Prix", "Country": "Mexico", "Location": "Mexico City", "EventFormat": "conventional"},
        {"RoundNumber": 19, "EventName": "Sao Paulo Grand Prix", "Country": "Brazil", "Location": "Interlagos", "EventFormat": "sprint"},
        {"RoundNumber": 20, "EventName": "Qatar Grand Prix", "Country": "Qatar", "Location": "Lusail", "EventFormat": "conventional"},
        {"RoundNumber": 21, "EventName": "Saudi Arabian Grand Prix", "Country": "Saudi Arabia", "Location": "Jeddah", "EventFormat": "conventional"},
        {"RoundNumber": 22, "EventName": "Abu Dhabi Grand Prix", "Country": "UAE", "Location": "Yas Marina", "EventFormat": "conventional"},
    ],
    2020: [
        {"RoundNumber": 1, "EventName": "Austrian Grand Prix", "Country": "Austria", "Location": "Spielberg", "EventFormat": "conventional"},
        {"RoundNumber": 2, "EventName": "Styrian Grand Prix", "Country": "Austria", "Location": "Spielberg", "EventFormat": "conventional"},
        {"RoundNumber": 3, "EventName": "Hungarian Grand Prix", "Country": "Hungary", "Location": "Budapest", "EventFormat": "conventional"},
        {"RoundNumber": 4, "EventName": "British Grand Prix", "Country": "Great Britain", "Location": "Silverstone", "EventFormat": "conventional"},
        {"RoundNumber": 5, "EventName": "70th Anniversary Grand Prix", "Country": "Great Britain", "Location": "Silverstone", "EventFormat": "conventional"},
        {"RoundNumber": 6, "EventName": "Spanish Grand Prix", "Country": "Spain", "Location": "Barcelona", "EventFormat": "conventional"},
        {"RoundNumber": 7, "EventName": "Belgian Grand Prix", "Country": "Belgium", "Location": "Spa-Francorchamps", "EventFormat": "conventional"},
        {"RoundNumber": 8, "EventName": "Italian Grand Prix", "Country": "Italy", "Location": "Monza", "EventFormat": "conventional"},
        {"RoundNumber": 9, "EventName": "Tuscan Grand Prix", "Country": "Italy", "Location": "Mugello", "EventFormat": "conventional"},
        {"RoundNumber": 10, "EventName": "Russian Grand Prix", "Country": "Russia", "Location": "Sochi", "EventFormat": "conventional"},
        {"RoundNumber": 11, "EventName": "Eifel Grand Prix", "Country": "Germany", "Location": "Nürburgring", "EventFormat": "conventional"},
        {"RoundNumber": 12, "EventName": "Portuguese Grand Prix", "Country": "Portugal", "Location": "Portimão", "EventFormat": "conventional"},
        {"RoundNumber": 13, "EventName": "Emilia Romagna Grand Prix", "Country": "Italy", "Location": "Imola", "EventFormat": "conventional"},
        {"RoundNumber": 14, "EventName": "Turkish Grand Prix", "Country": "Turkey", "Location": "Istanbul", "EventFormat": "conventional"},
        {"RoundNumber": 15, "EventName": "Bahrain Grand Prix", "Country": "Bahrain", "Location": "Sakhir", "EventFormat": "conventional"},
        {"RoundNumber": 16, "EventName": "Sakhir Grand Prix", "Country": "Bahrain", "Location": "Sakhir Outer", "EventFormat": "conventional"},
        {"RoundNumber": 17, "EventName": "Abu Dhabi Grand Prix", "Country": "UAE", "Location": "Yas Marina", "EventFormat": "conventional"},
    ]
}

def get_season_events(year: int) -> List[Dict[str, Any]]:
    """
    Fetches the Grand Prix calendar for a given season.
    Returns the exact official schedule for 2020 to 2024.
    """
    if FASTF1_AVAILABLE:
        try:
            schedule = fastf1.get_event_schedule(year, include_testing=False)
            if schedule is not None and not schedule.empty:
                events = []
                for _, row in schedule.iterrows():
                    event_name = str(row.get("EventName", ""))
                    round_num = row.get("RoundNumber", 0)
                    country = str(row.get("Country", ""))
                    location = str(row.get("Location", ""))
                    event_format = str(row.get("EventFormat", "conventional"))
                    if event_name and round_num > 0:
                        events.append({
                            "RoundNumber": int(round_num),
                            "EventName": event_name,
                            "Country": country,
                            "Location": location,
                            "EventFormat": event_format
                        })
                if events:
                    return events
        except Exception as e:
            logger.warning(f"FastF1 schedule query: {e}")

    # Fallback to verified calendar for that specific year
    return OFFICIAL_CALENDARS.get(year, OFFICIAL_CALENDARS.get(2024, []))

def get_session_types() -> List[str]:
    """Returns valid session options."""
    return ["Race", "Qualifying", "Sprint", "Practice 1", "Practice 2", "Practice 3"]

ALIASES = {
    'british': 'great britain',
    'italian': 'italy',
    'spanish': 'spain',
    'japanese': 'japan',
    'sao paulo': 'brazil',
    'brazil': 'brazil',
    'mexico city': 'mexico',
    'united states': 'usa',
    'emilia romagna': 'italy',
    'austrian': 'austria',
    'australian': 'australia',
    'belgian': 'belgium',
    'dutch': 'netherlands',
    'hungarian': 'hungary',
    'canadian': 'canada',
    'saudi arabian': 'saudi arabia',
    'chinese': 'china'
}

def match_openf1_session(available_sessions: list, target: str) -> Optional[dict]:
    """Matches user selected session name to OpenF1 session dictionary."""
    t = target.lower().strip()
    for s in available_sessions:
        name = s.get('session_name', '').lower().strip()
        stype = s.get('session_type', '').lower().strip()
        if t == 'sprint':
            if name == 'sprint' or (stype == 'race' and 'sprint' in name and 'qualifying' not in name and 'shootout' not in name):
                return s
        elif t == 'qualifying':
            if name == 'qualifying' or (stype == 'qualifying' and 'sprint' not in name):
                return s
        elif t == 'race':
            if name == 'race' or (stype == 'race' and 'sprint' not in name):
                return s
        elif t in ['practice 1', 'fp1']:
            if 'practice 1' in name or 'fp1' in name:
                return s
        elif t in ['practice 2', 'fp2']:
            if 'practice 2' in name or 'fp2' in name:
                return s
        elif t in ['practice 3', 'fp3']:
            if 'practice 3' in name or 'fp3' in name:
                return s
        elif t in name or name in t:
            return s
    return None

def fetch_openf1_session(year: int, grand_prix: str, session_type: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves official F1 session timing, stints, classification, and weather from OpenF1 API
    with local disk caching and robust failovers.
    """
    clean_gp = re.sub(r'[^a-zA-Z0-9]', '_', grand_prix)
    clean_sess = re.sub(r'[^a-zA-Z0-9]', '_', session_type)
    cache_path = os.path.join(CACHE_DIR, f"openf1_{year}_{clean_gp}_{clean_sess}.pkl")

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                cached_data = pickle.load(f)
                logger.info(f"Loaded OpenF1 session from local cache: {cache_path}")
                return cached_data
        except Exception as e:
            logger.warning(f"Could not read OpenF1 cache: {e}")

    try:
        # 1. Locate Meeting with hierarchical matching
        r_m = _safe_openf1_query("meetings", {"year": year})
        if not r_m:
            return None

        gp_lower = grand_prix.lower().strip()
        matched_m = None

        # Step 1: Substring/exact match on meeting name
        for m in r_m:
            m_name = m.get("meeting_name", "").lower()
            if "testing" in m_name:
                continue
            if gp_lower == m_name or gp_lower in m_name or m_name in gp_lower:
                matched_m = m
                break

        # Step 2: Country name or alias lookup
        if not matched_m:
            for m in r_m:
                m_name = m.get("meeting_name", "").lower()
                if "testing" in m_name:
                    continue
                c_name = m.get("country_name", "").lower()
                for k, v in ALIASES.items():
                    if k in gp_lower and (k in m_name or v in m_name or v == c_name):
                        matched_m = m
                        break
                if matched_m:
                    break

        if not matched_m:
            logger.warning(f"No OpenF1 meeting found for {year} {grand_prix}")
            return None

        m_key = matched_m["meeting_key"]

        # 2. Locate Session with sprint/qualifying aware matching
        r_s = _safe_openf1_query("sessions", {"meeting_key": m_key})
        if not r_s:
            return None

        matched_s = match_openf1_session(r_s, session_type)
        if not matched_s:
            logger.warning(f"Session {session_type} not found in OpenF1 meeting {m_key}")
            return None

        s_key = matched_s["session_key"]

        # 3. Drivers
        drivers = _safe_openf1_query("drivers", {"session_key": s_key}) or []
        driver_map = {}
        for d in drivers:
            num = d.get("driver_number")
            code = d.get("name_acronym", f"D{num}")
            driver_map[num] = {
                "code": code,
                "name": d.get("broadcast_name", f"Driver {num}"),
                "team": d.get("team_name", "Unknown"),
                "number": num
            }

        # 4. Stints (None-safe parsing for formation lap DNFs)
        stints = _safe_openf1_query("stints", {"session_key": s_key}) or []
        stint_map = {}
        if stints:
            for s in stints:
                num = s.get("driver_number")
                comp = s.get("compound", "MEDIUM") or "MEDIUM"
                s_num = s.get("stint_number") or 1
                l_start = s.get("lap_start")
                l_end = s.get("lap_end")
                if l_start is None:
                    continue
                if l_end is None:
                    l_end = l_start
                for l in range(int(l_start), int(l_end) + 1):
                    stint_map[(num, l)] = {
                        "compound": comp,
                        "stint": s_num,
                        "tyre_life": max(1, l - int(l_start) + 1)
                    }

        # 5. Laps
        laps_raw = _safe_openf1_query("laps", {"session_key": s_key}, timeout=15)
        if not laps_raw:
            return None

        laps_df = pd.DataFrame(laps_raw)
        laps_df = laps_df.dropna(subset=["lap_duration"])
        laps_df = laps_df[laps_df["lap_duration"] > 25.0]  # Filter invalid timestamps
        if laps_df.empty:
            return None

        laps_df["Driver"] = laps_df["driver_number"].map(lambda n: driver_map.get(n, {}).get("code", str(n)))
        laps_df["LapNumber"] = laps_df["lap_number"]
        laps_df["LapTimeSeconds"] = laps_df["lap_duration"]
        laps_df["LapTime"] = pd.to_timedelta(laps_df["LapTimeSeconds"], unit="s")
        laps_df["Sector1Seconds"] = laps_df.get("duration_sector_1", np.nan)
        laps_df["Sector2Seconds"] = laps_df.get("duration_sector_2", np.nan)
        laps_df["Sector3Seconds"] = laps_df.get("duration_sector_3", np.nan)
        laps_df["IsPitOut"] = laps_df.get("is_pit_out_lap", pd.Series([False]*len(laps_df))).fillna(False)
        laps_df["IsPitIn"] = False

        stint_records = [
            stint_map.get((row["driver_number"], row["lap_number"]), {"compound": "MEDIUM", "stint": 1, "tyre_life": row["lap_number"]})
            for _, row in laps_df.iterrows()
        ]
        laps_df["Compound"] = [x["compound"] for x in stint_records]
        laps_df["Stint"] = [x["stint"] for x in stint_records]
        laps_df["TyreLife"] = [x["tyre_life"] for x in stint_records]
        laps_df["TrackStatus"] = "1"

        # 6. Weather
        weather_raw = _safe_openf1_query("weather", {"session_key": s_key}) or []
        weather_df = pd.DataFrame(weather_raw)
        if not weather_df.empty:
            weather_df["Time"] = pd.to_datetime(weather_df["date"], format='ISO8601')
            weather_df["AirTemp"] = weather_df.get("air_temperature", 25.0)
            weather_df["TrackTemp"] = weather_df.get("track_temperature", 32.0)
            weather_df["Humidity"] = weather_df.get("humidity", 50.0)
            weather_df["WindSpeed"] = weather_df.get("wind_speed", 10.0)
            weather_df["Rainfall"] = weather_df.get("rainfall", 0) > 0
        else:
            weather_df = pd.DataFrame()

        # 7. Positions and Classification
        pos_raw = _safe_openf1_query("position", {"session_key": s_key}) or []
        results_rows = []
        if pos_raw:
            pos_df = pd.DataFrame(pos_raw)
            pos_df["dt"] = pd.to_datetime(pos_df["date"], format='ISO8601')
            first_pos = pos_df.sort_values("dt").groupby("driver_number").first()["position"].to_dict()
            last_pos = pos_df.sort_values("dt").groupby("driver_number").last()["position"].to_dict()
            
            for num, info in driver_map.items():
                results_rows.append({
                    "code": info["code"],
                    "name": info["name"],
                    "team": info["team"],
                    "grid": int(first_pos.get(num, 20)),
                    "pos": int(last_pos.get(num, 20)),
                    "status": "Finished"
                })

        # Practice / Qualifying fallback: rank by fastest lap time
        if not results_rows and not laps_df.empty:
            driver_fastest = laps_df.groupby("Driver")["LapTimeSeconds"].min().sort_values().reset_index()
            code_to_num = {info["code"]: num for num, info in driver_map.items()}
            for rank_idx, r in enumerate(driver_fastest.itertuples(), 1):
                code = r.Driver
                num = code_to_num.get(code, 0)
                info = driver_map.get(num, {})
                results_rows.append({
                    "code": code,
                    "name": info.get("name", code),
                    "team": info.get("team", "Unknown"),
                    "grid": rank_idx,
                    "pos": rank_idx,
                    "status": "Classified"
                })

        results_df = pd.DataFrame(results_rows).sort_values("pos") if results_rows else pd.DataFrame()

        # Fastest Lap
        valid_laps = laps_df[laps_df["LapTimeSeconds"] > 40.0]
        if not valid_laps.empty:
            fastest_lap_row = valid_laps.loc[valid_laps["LapTimeSeconds"].idxmin()]
            from utils.formatting import format_seconds_to_laptime
            fastest_lap_str = format_seconds_to_laptime(fastest_lap_row["LapTimeSeconds"])
            fastest_driver = str(fastest_lap_row["Driver"])
        else:
            fastest_lap_str = "N/A"
            fastest_driver = "N/A"

        session_dict = {
            "event_name": grand_prix,
            "official_name": matched_m.get("meeting_name", grand_prix),
            "circuit_name": matched_s.get("circuit_short_name", f"{grand_prix} Circuit"),
            "country": matched_m.get("country_name", ""),
            "location": matched_m.get("location", ""),
            "season": year,
            "round": matched_m.get("meeting_key", 1),
            "date": str(matched_s.get("date_start", f"{year}"))[:10],
            "session_type": session_type,
            "total_laps": int(laps_df["LapNumber"].max()),
            "fastest_lap": fastest_lap_str,
            "fastest_driver": fastest_driver,
            "safety_cars": 0,
            "vsc": 0,
            "results": results_df,
            "laps": laps_df,
            "weather": weather_df,
            "openf1_session_key": s_key,
            "driver_num_map": {info["code"]: num for num, info in driver_map.items()},
            "is_synthetic": False,
            "load_message": f"Successfully retrieved official timing & telemetry for {year} {grand_prix} ({session_type}) via OpenF1."
        }

        # Save to disk cache
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(session_dict, f)
        except Exception as e:
            logger.warning(f"Could not write OpenF1 cache: {e}")

        return session_dict
    except Exception as e:
        logger.warning(f"OpenF1 session fetch error: {e}")
        return None

def load_f1_session_data(year: int, grand_prix: str, session_type: str, force_demo: bool = False) -> Dict[str, Any]:
    """
    Main ingestion function.
    1. If force_demo, returns synthetic demo dataset.
    2. Checks local disk cache for instantaneous loading.
    3. For modern seasons (2023+), uses OpenF1 directly to avoid 401 paywall blocks on Formula1.com.
    4. For historical archives, leverages FastF1.
    5. Gracefully falls back to high-fidelity synthetic demo dataset with clear integrity flag if offline.
    """
    if force_demo:
        demo = generate_sample_race_data()
        demo["is_synthetic"] = True
        demo["load_message"] = "Demo Mode: High-fidelity synthetic dataset loaded."
        return demo

    # Check local disk cache first (instant response)
    clean_gp = re.sub(r'[^a-zA-Z0-9]', '_', grand_prix)
    clean_sess = re.sub(r'[^a-zA-Z0-9]', '_', session_type)
    cache_path = os.path.join(CACHE_DIR, f"openf1_{year}_{clean_gp}_{clean_sess}.pkl")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                cached = pickle.load(f)
                cached["load_message"] = f"Loaded official timing data from local cache ({year} {grand_prix})."
                return cached
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")

    # For 2023-2024+, query OpenF1 first to prevent F1 livetiming 401 delays
    if year >= 2023:
        openf1_data = fetch_openf1_session(year, grand_prix, session_type)
        if openf1_data is not None:
            return openf1_data

    # FastF1 loader
    if FASTF1_AVAILABLE:
        try:
            logger.info(f"Loading FastF1 session: {year} - {grand_prix} - {session_type}")
            code_map = {
                "Race": "R",
                "Qualifying": "Q",
                "Sprint": "S",
                "Practice 1": "FP1",
                "Practice 2": "FP2",
                "Practice 3": "FP3"
            }
            session_code = code_map.get(session_type, session_type)
            session = None
            try:
                session = fastf1.get_session(year, grand_prix, session_code)
            except Exception:
                if session_type == "Sprint":
                    for alt in ["Sprint", "Sprint Qualifying", "SQ"]:
                        try:
                            session = fastf1.get_session(year, grand_prix, alt)
                            break
                        except Exception:
                            continue
            if session is None:
                session = fastf1.get_session(year, grand_prix, session_code)

            try:
                session.load(laps=True, telemetry=True, weather=True, messages=False)
            except Exception as load_err:
                logger.warning(f"Telemetry load encountered an issue ({load_err}); falling back to laps & weather")
                session.load(laps=True, telemetry=False, weather=True, messages=False)

            if session.laps is None or session.laps.empty:
                raise ValueError("Session laps empty from FastF1 source")

            laps = session.laps.copy()
            if "LapTime" in laps.columns:
                laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
            if "Sector1Time" in laps.columns:
                laps["Sector1Seconds"] = laps["Sector1Time"].dt.total_seconds()
            if "Sector2Time" in laps.columns:
                laps["Sector2Seconds"] = laps["Sector2Time"].dt.total_seconds()
            if "Sector3Time" in laps.columns:
                laps["Sector3Seconds"] = laps["Sector3Time"].dt.total_seconds()

            if "Compound" not in laps.columns or laps["Compound"].isna().all():
                laps["Compound"] = "MEDIUM"

            results = session.results.copy() if session.results is not None else pd.DataFrame()
            weather = session.weather_data.copy() if session.weather_data is not None else pd.DataFrame()

            fastest_lap_obj = laps.pick_fastest()
            fastest_lap_str = "N/A"
            fastest_driver = "N/A"
            if fastest_lap_obj is not None and not pd.isna(fastest_lap_obj["LapTimeSeconds"]):
                from utils.formatting import format_seconds_to_laptime
                fastest_lap_str = format_seconds_to_laptime(fastest_lap_obj["LapTimeSeconds"])
                fastest_driver = str(fastest_lap_obj.get("Driver", "N/A"))

            sc_count = 0
            vsc_count = 0
            if "TrackStatus" in laps.columns:
                sc_count = laps["TrackStatus"].astype(str).str.contains("4").sum() // 20
                vsc_count = laps["TrackStatus"].astype(str).str.contains("6").sum() // 20

            circuit_name = getattr(session.event, "CircuitName", f"{grand_prix} Circuit")
            country = getattr(session.event, "Country", "")
            location = getattr(session.event, "Location", "")
            event_date = str(getattr(session.event, "EventDate", f"{year}"))[:10]

            session_dict = {
                "event_name": grand_prix,
                "official_name": getattr(session.event, "OfficialEventName", grand_prix),
                "circuit_name": circuit_name,
                "country": country,
                "location": location,
                "season": year,
                "round": getattr(session.event, "RoundNumber", 1),
                "date": event_date,
                "session_type": session_type,
                "total_laps": int(laps["LapNumber"].max()) if not laps.empty else 0,
                "fastest_lap": fastest_lap_str,
                "fastest_driver": fastest_driver,
                "safety_cars": max(0, sc_count),
                "vsc": max(0, vsc_count),
                "results": results,
                "laps": laps,
                "weather": weather,
                "fastf1_session": session,
                "is_synthetic": False,
                "load_message": f"Successfully loaded real FastF1 session data for {year} {grand_prix} ({session_type})."
            }

            # Cache to local disk for instant future retrieval
            try:
                with open(cache_path, "wb") as f:
                    pickle.dump(session_dict, f)
            except Exception as e:
                logger.warning(f"Could not write cache: {e}")

            return session_dict
        except Exception as e:
            logger.warning(f"FastF1 load did not succeed ({e}). Transitioning to OpenF1 official provider.")

    # Attempt 2: OpenF1 Official Provider
    openf1_data = fetch_openf1_session(year, grand_prix, session_type)
    if openf1_data is not None:
        return openf1_data

    # Attempt 3: Graceful Offline Fallback
    logger.info("External timing APIs unreachable or session unavailable. Falling back to synthetic demo suite.")
    demo = generate_sample_race_data()
    demo["is_synthetic"] = True
    demo["load_message"] = "External F1 timing servers unreachable or session not published. Displaying high-fidelity synthetic demo data."
    return demo

def get_driver_fastest_telemetry(session_data: Dict[str, Any], driver_code: str) -> Optional[pd.DataFrame]:
    """
    Extracts high-resolution telemetry for a driver's fastest lap in the loaded session.
    """
    if session_data.get("is_synthetic", False):
        tel_dict = session_data.get("telemetry", {})
        if driver_code in tel_dict:
            return tel_dict[driver_code].copy()
        return generate_telemetry_profile(driver_code)

    # 1. Check if OpenF1 session
    if "openf1_session_key" in session_data:
        s_key = session_data["openf1_session_key"]
        d_map = session_data.get("driver_num_map", {})
        d_num = d_map.get(driver_code)

        if d_num is not None:
            cache_tel_path = os.path.join(CACHE_DIR, f"openf1_tel_{s_key}_{driver_code}.pkl")
            if os.path.exists(cache_tel_path):
                try:
                    with open(cache_tel_path, "rb") as f:
                        return pickle.load(f)
                except Exception:
                    pass

            try:
                laps = session_data["laps"]
                d_laps = laps[laps["Driver"] == driver_code].dropna(subset=["LapTimeSeconds"])
                if not d_laps.empty:
                    fastest_row = d_laps.loc[d_laps["LapTimeSeconds"].idxmin()]
                    t_start = pd.to_datetime(fastest_row.get("date_start", ""))
                    t_end = t_start + pd.to_timedelta(fastest_row["LapTimeSeconds"], unit="s")
                    start_iso = t_start.strftime("%Y-%m-%dT%H:%M:%S")
                    end_iso = t_end.strftime("%Y-%m-%dT%H:%M:%S")

                    r_car = _safe_openf1_query("car_data", {"session_key": s_key, "driver_number": d_num, "date>=": start_iso, "date<=": end_iso}, timeout=10)
                    r_loc = _safe_openf1_query("location", {"session_key": s_key, "driver_number": d_num, "date>=": start_iso, "date<=": end_iso}, timeout=10)

                    if r_car and r_loc:
                        df_car = pd.DataFrame(r_car)
                        df_loc = pd.DataFrame(r_loc)
                        df_car["dt"] = pd.to_datetime(df_car["date"], format='ISO8601')
                        df_loc["dt"] = pd.to_datetime(df_loc["date"], format='ISO8601')

                        merged = pd.merge_asof(df_car.sort_values("dt"), df_loc.sort_values("dt")[["dt", "x", "y"]], on="dt", direction="nearest")
                        
                        v_ms = merged["speed"] * (1000.0 / 3600.0)
                        dt_sec = merged["dt"].diff().dt.total_seconds().fillna(0.25)
                        merged["Distance"] = np.cumsum(v_ms * dt_sec)
                        merged["Speed"] = merged["speed"]
                        merged["Throttle"] = merged["throttle"]
                        merged["Brake"] = merged["brake"]
                        merged["nGear"] = merged["n_gear"]
                        merged["RPM"] = merged["rpm"]
                        merged["X"] = merged["x"]
                        merged["Y"] = merged["y"]
                        merged["Driver"] = driver_code

                        # Cache telemetry
                        try:
                            with open(cache_tel_path, "wb") as f:
                                pickle.dump(merged, f)
                        except Exception:
                            pass

                        return merged
            except Exception as e:
                logger.warning(f"Error fetching OpenF1 telemetry for {driver_code}: {e}")

    # 2. Check FastF1 session
    session = session_data.get("fastf1_session")
    if session is not None and session.laps is not None and not session.laps.empty:
        try:
            driver_laps = session.laps.pick_driver(driver_code)
            if not driver_laps.empty:
                fastest_lap = driver_laps.pick_fastest()
                if fastest_lap is not None and not pd.isna(fastest_lap.get("LapTime")):
                    telemetry = fastest_lap.get_telemetry()
                    if telemetry is not None and not telemetry.empty:
                        df = telemetry.copy()
                        df["Driver"] = driver_code
                        return df
        except Exception as e:
            logger.warning(f"FastF1 fastest lap telemetry error for {driver_code}: {e}")

    return generate_telemetry_profile(driver_code)

def synchronize_telemetry_by_distance(
    tel1: pd.DataFrame, 
    tel2: pd.DataFrame, 
    num_points: int = 1000
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Interpolates two driver telemetry streams onto a standardized uniform distance grid.
    Returns (synced_driver1, synced_driver2, delta_df).
    """
    max_d = min(tel1["Distance"].max(), tel2["Distance"].max())
    min_d = max(tel1["Distance"].min(), tel2["Distance"].min())
    grid_distance = np.linspace(min_d, max_d, num_points)

    def interpolate_stream(tel: pd.DataFrame, driver_label: str) -> pd.DataFrame:
        clean = tel.dropna(subset=["Distance"]).sort_values("Distance").drop_duplicates(subset=["Distance"])
        res = pd.DataFrame({"Distance": grid_distance})
        
        for col in ["Speed", "Throttle", "Brake", "nGear", "RPM", "X", "Y"]:
            if col in clean.columns:
                res[col] = np.interp(grid_distance, clean["Distance"], clean[col])
            else:
                res[col] = 0.0

        res["Driver"] = driver_label
        return res

    d1_code = str(tel1.get("Driver", pd.Series(["D1"])).iloc[0])
    d2_code = str(tel2.get("Driver", pd.Series(["D2"])).iloc[0])

    s1 = interpolate_stream(tel1, d1_code)
    s2 = interpolate_stream(tel2, d2_code)

    # Compute delta speed and estimated time delta
    delta_speed = s1["Speed"] - s2["Speed"]
    v1_ms = np.maximum(s1["Speed"] * (1000.0 / 3600.0), 5.0)
    v2_ms = np.maximum(s2["Speed"] * (1000.0 / 3600.0), 5.0)
    dx = np.gradient(grid_distance)
    dt1 = dx / v1_ms
    dt2 = dx / v2_ms
    cum_time1 = np.cumsum(dt1)
    cum_time2 = np.cumsum(dt2)
    time_delta = cum_time1 - cum_time2

    delta_df = pd.DataFrame({
        "Distance": grid_distance,
        "DeltaSpeed": np.round(delta_speed, 2),
        "DeltaTime": np.round(time_delta, 3),
        "D1": d1_code,
        "D2": d2_code
    })

    return s1, s2, delta_df
