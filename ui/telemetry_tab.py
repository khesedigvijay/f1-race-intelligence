"""
Speed and Telemetry Analysis Tab Component.
Distance-synchronized driver vs driver telemetry traces, delta time, braking zones, and corner apex speeds.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.f1_data import get_driver_fastest_telemetry, synchronize_telemetry_by_distance
from analysis.telemetry import detect_braking_zones, detect_apexes, compute_telemetry_metrics
from ui.theme import apply_f1_plot_theme, render_metric_card
from utils.formatting import get_team_color

def render_telemetry_tab(session_data: dict):
    """Renders the Speed & Telemetry Analysis tab."""
    st.markdown("### 🏎️ High-Resolution Lap Telemetry Analysis")
    st.caption("Synchronized by track distance (meters) for precise apex, braking, and delta-speed comparison.")

    laps = session_data.get("laps", pd.DataFrame())
    if laps.empty or "Driver" not in laps.columns:
        st.warning("No lap timing or telemetry available for this session.")
        return

    available_drivers = sorted(laps["Driver"].unique())
    if len(available_drivers) < 2:
        available_drivers = ["VER", "LEC"]

    # Select drivers
    c_d1, c_d2 = st.columns(2)
    with c_d1:
        d1 = st.selectbox("Primary Driver (Reference)", available_drivers, index=0, key="tel_d1")
    with c_d2:
        default_idx = 1 if len(available_drivers) > 1 else 0
        d2 = st.selectbox("Comparison Driver", available_drivers, index=default_idx, key="tel_d2")

    # Fetch fastest lap telemetry
    with st.spinner("Synchronizing telemetry traces..."):
        tel1 = get_driver_fastest_telemetry(session_data, d1)
        tel2 = get_driver_fastest_telemetry(session_data, d2)

    if tel1 is None or tel2 is None or tel1.empty or tel2.empty:
        st.warning("Telemetry could not be retrieved for one of the selected drivers.")
        return

    # Synchronize by distance
    s1, s2, delta_df = synchronize_telemetry_by_distance(tel1, tel2)
    metrics = compute_telemetry_metrics(s1, s2)

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(render_metric_card(f"{d1} Top Speed", f"{metrics['d1_top_speed']} km/h", f"Mean: {metrics['d1_mean_speed']} km/h"), unsafe_allow_html=True)
    with m2:
        st.markdown(render_metric_card(f"{d2} Top Speed", f"{metrics['d2_top_speed']} km/h", f"Mean: {metrics['d2_mean_speed']} km/h", delta_color="#E10600"), unsafe_allow_html=True)
    with m3:
        st.markdown(render_metric_card(f"{d1} Full Throttle", f"{metrics['d1_full_throttle_pct']}%", f"Braking: {metrics['d1_braking_pct']}%"), unsafe_allow_html=True)
    with m4:
        st.markdown(render_metric_card(f"{d2} Full Throttle", f"{metrics['d2_full_throttle_pct']}%", f"Braking: {metrics['d2_braking_pct']}%", delta_color="#E10600"), unsafe_allow_html=True)

    # Multi-panel Stacked Telemetry Chart
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(
            "Speed (km/h)",
            f"Delta Time ({d1} vs {d2}) (s)",
            "Throttle (%)",
            "Brake Application",
            "Gear"
        ),
        row_heights=[0.35, 0.18, 0.17, 0.15, 0.15]
    )

    color_d1 = "#00D2BE"
    color_d2 = "#E10600"

    # Panel 1: Speed
    fig.add_trace(go.Scatter(x=s1["Distance"], y=s1["Speed"], name=d1, line=dict(color=color_d1, width=2.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=s2["Distance"], y=s2["Speed"], name=d2, line=dict(color=color_d2, width=2.0)), row=1, col=1)

    # Panel 2: Delta Time
    fig.add_trace(go.Scatter(
        x=delta_df["Distance"], y=delta_df["DeltaTime"], name="Time Delta",
        line=dict(color="#FFDF00", width=1.8),
        fill="tozeroy",
        fillcolor="rgba(255, 223, 0, 0.15)"
    ), row=2, col=1)

    # Panel 3: Throttle
    fig.add_trace(go.Scatter(x=s1["Distance"], y=s1["Throttle"], name=f"{d1} Throttle", line=dict(color=color_d1, width=1.5), showlegend=False), row=3, col=1)
    fig.add_trace(go.Scatter(x=s2["Distance"], y=s2["Throttle"], name=f"{d2} Throttle", line=dict(color=color_d2, width=1.5), showlegend=False), row=3, col=1)

    # Panel 4: Brake
    fig.add_trace(go.Scatter(x=s1["Distance"], y=s1["Brake"], name=f"{d1} Brake", line=dict(color=color_d1, width=1.5), showlegend=False), row=4, col=1)
    fig.add_trace(go.Scatter(x=s2["Distance"], y=s2["Brake"], name=f"{d2} Brake", line=dict(color=color_d2, width=1.5), showlegend=False), row=4, col=1)

    # Panel 5: Gear
    fig.add_trace(go.Scatter(x=s1["Distance"], y=s1["nGear"], name=f"{d1} Gear", line=dict(color=color_d1, width=1.5), showlegend=False), row=5, col=1)
    fig.add_trace(go.Scatter(x=s2["Distance"], y=s2["nGear"], name=f"{d2} Gear", line=dict(color=color_d2, width=1.5), showlegend=False), row=5, col=1)

    fig.update_xaxes(title_text="Track Distance (Meters)", row=5, col=1)
    apply_f1_plot_theme(fig, title="", height=680)
    st.plotly_chart(fig, use_container_width=True)

    # Detailed Braking Zones & Corner Apexes Table
    st.markdown("### 🛑 Corner Apex & Braking Zone Breakdown")
    c_brake, c_apex = st.columns(2)
    
    with c_brake:
        st.markdown(f"**{d1} Significant Braking Events**")
        b_zones = detect_braking_zones(s1)
        if b_zones:
            st.dataframe(pd.DataFrame(b_zones), use_container_width=True, height=260)
        else:
            st.info("No distinct braking events isolated.")

    with c_apex:
        st.markdown(f"**{d1} Corner Apex Velocities**")
        apexes = detect_apexes(s1)
        if apexes:
            st.dataframe(pd.DataFrame(apexes), use_container_width=True, height=260)
        else:
            st.info("Apex detection completed.")
