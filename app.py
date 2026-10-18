"""
Formula 1 Race Intelligence Dashboard.
Main Streamlit application entry point.
"""

import streamlit as st
import pandas as pd
import numpy as np

# Set page configuration first
st.set_page_config(
    page_title="F1 Race Intelligence Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply UI Styling
from ui.theme import inject_f1_theme
inject_f1_theme()

# Import Utilities and Tab Views
from utils.f1_data import (
    get_available_seasons,
    get_season_events,
    get_session_types,
    load_f1_session_data,
    FASTF1_AVAILABLE
)
from data.database import add_user_note, get_user_notes

from ui.overview_tab import render_overview_tab
from ui.telemetry_tab import render_telemetry_tab
from ui.tire_tab import render_tire_tab
from ui.evolution_tab import render_evolution_tab
from ui.laps_tab import render_laps_tab
from ui.circuit_tab import render_circuit_tab
from ui.strategy_tab import render_strategy_tab
from ui.weather_tab import render_weather_tab
from ui.analytics_tab import render_analytics_tab
from ui.ml_tab import render_ml_tab
from ui.explorer_tab import render_explorer_tab

# Initialize session state for cached data
if "session_data" not in st.session_state:
    st.session_state["session_data"] = None
if "current_session_key" not in st.session_state:
    st.session_state["current_session_key"] = None

# Sidebar - Session Navigation and Parameters
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            <span style="font-size: 2rem;">🏎️</span>
            <div>
                <h2 style="margin: 0; padding: 0; color: #FFFFFF; font-size: 1.3rem; letter-spacing: 0.5px;">F1 RACE INTELLIGENCE</h2>
                <span style="color: #E10600; font-size: 0.72rem; font-weight: 800; letter-spacing: 1.5px;">PIT WALL TELEMETRY & ML</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### ⚙️ Session Selector")

    # Season
    seasons = get_available_seasons()
    selected_season = st.selectbox("Season", seasons, index=0)

    # Grand Prix Calendar
    events = get_season_events(selected_season)
    event_names = [e["EventName"] for e in events]
    selected_gp = st.selectbox("Grand Prix", event_names, index=0)

    # Session Type
    session_types = get_session_types()
    selected_session = st.selectbox("Session", session_types, index=0)

    # Demo Mode Override
    force_demo = st.checkbox("Force Demo Mode (Offline)", value=not FASTF1_AVAILABLE, help="Loads rich synthetic Bahrain 2024 GP data without querying external servers.")

    # Load Button
    load_clicked = st.button("🚀 Load Intelligence Data", use_container_width=True)

    session_key = f"{selected_season}_{selected_gp}_{selected_session}_{force_demo}"

    # Auto-load on startup if nothing loaded yet, when user clicks button, or when selectors change
    if st.session_state["session_data"] is None or load_clicked or session_key != st.session_state.get("current_session_key"):
        with st.spinner("Retrieving timing sheets and telemetry streams..."):
            session_data = load_f1_session_data(
                year=selected_season,
                grand_prix=selected_gp,
                session_type=selected_session,
                force_demo=force_demo
            )
            st.session_state["session_data"] = session_data
            st.session_state["current_session_key"] = session_key

    st.markdown("---")
    
    # Engine & Source Status
    st.markdown("### 📡 Telemetry Telecommunications")
    current_data = st.session_state.get("session_data")
    if current_data and not current_data.get("is_synthetic", False):
        st.markdown('<span class="badge-live">ONLINE: OFFICIAL F1 TIMING</span>', unsafe_allow_html=True)
        st.caption("Active connection to official FIA timing records & disk cache.")
    else:
        st.markdown('<span class="badge-demo">OFFLINE / SYNTHETIC DEMO</span>', unsafe_allow_html=True)
        st.caption("Rendering high-fidelity Bahrain 2024 demo profile.")

    # User Observation Notes Area
    st.markdown("---")
    with st.expander("📝 Pit Wall Observation Log", expanded=False):
        note_driver = st.text_input("Driver Code", value="VER", max_chars=3)
        note_lap = st.number_input("Lap Number", min_value=1, max_value=80, value=15)
        note_content = st.text_area("Observation Notes", placeholder="e.g. Front wing flap adjustment at pit stop...")
        if st.button("Save Observation"):
            if note_content.strip():
                add_user_note(st.session_state["current_session_key"] or "default", note_driver, int(note_lap), note_content.strip())
                st.success("Note logged to local SQLite store.")
        
        # Display existing notes
        notes = get_user_notes(st.session_state["current_session_key"] or "default")
        if notes:
            st.markdown("**Logged Notes:**")
            for n in notes[-3:]:
                st.caption(f"**L{n['lap']} [{n['driver']}]:** {n['note']}")

# Retrieve active session data
active_data = st.session_state.get("session_data")

if active_data is None:
    st.info("Please select a session and click 'Load Intelligence Data'.")
    st.stop()

# Notification Bar
load_msg = active_data.get("load_message", "")
if load_msg:
    if active_data.get("is_synthetic", False):
        st.warning(f"⚠️ {load_msg}")
    else:
        st.success(f"✅ {load_msg}")

# Navigation Tabs
tab_overview, tab_tel, tab_tire, tab_evol, tab_laps, tab_circuit, tab_strat, tab_weather, tab_rank, tab_ml, tab_explorer = st.tabs([
    "🏁 Race Overview",
    "⚡ Telemetry",
    "🛞 Tire Degradation",
    "🛣️ Track Evolution",
    "⏱️ Lap Progression",
    "🗺️ Circuit Map",
    "🔮 Strategy Simulator",
    "🌤️ Weather",
    "🏆 Driver Rankings",
    "🤖 ML Predictions",
    "📑 Data Explorer"
])

with tab_overview:
    render_overview_tab(active_data)

with tab_tel:
    render_telemetry_tab(active_data)

with tab_tire:
    render_tire_tab(active_data)

with tab_evol:
    render_evolution_tab(active_data)

with tab_laps:
    render_laps_tab(active_data)

with tab_circuit:
    render_circuit_tab(active_data)

with tab_strat:
    render_strategy_tab(active_data)

with tab_weather:
    render_weather_tab(active_data)

with tab_rank:
    render_analytics_tab(active_data)

with tab_ml:
    render_ml_tab(active_data)

with tab_explorer:
    render_explorer_tab(active_data)
