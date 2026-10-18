"""
Interactive Circuit Map Tab Component.
Renders GPS/telemetry coordinates (X, Y) colored by speed, throttle, braking, or gear with corner markers.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.f1_data import get_driver_fastest_telemetry
from analysis.telemetry import detect_apexes
from ui.theme import apply_f1_plot_theme

def render_circuit_tab(session_data: dict):
    """Renders the Interactive Circuit Map tab."""
    st.markdown("### 🗺️ Interactive Circuit Track Map")
    st.caption("2D telemetry coordinates mapped with continuous velocity, throttle, braking, and gear telemetry heatmaps.")

    laps = session_data.get("laps", pd.DataFrame())
    available_drivers = sorted(laps["Driver"].unique()) if not laps.empty and "Driver" in laps.columns else ["VER", "LEC"]

    c_drv, c_metric = st.columns(2)
    with c_drv:
        driver = st.selectbox("Select Driver", available_drivers, index=0, key="circuit_driver")
    with c_metric:
        color_metric = st.selectbox(
            "Color Track By Telemetry Variable",
            options=["Speed", "Throttle", "Brake", "nGear"],
            format_func=lambda x: {
                "Speed": "Velocity (Speed km/h)",
                "Throttle": "Throttle Application (%)",
                "Brake": "Braking Intensity",
                "nGear": "Gear Selection (1-8)"
            }.get(x, x),
            key="circuit_metric"
        )

    # Fetch telemetry
    tel = get_driver_fastest_telemetry(session_data, driver)
    if tel is None or tel.empty or "X" not in tel.columns or "Y" not in tel.columns:
        st.warning("Coordinate telemetry (X, Y) unavailable for this driver.")
        return

    # Color scale mapping
    colorscales = {
        "Speed": "Turbo",
        "Throttle": "Greens",
        "Brake": "Reds",
        "nGear": "Plasma"
    }

    fig = go.Figure()

    # Base track scatter line with continuous color
    fig.add_trace(go.Scatter(
        x=tel["X"],
        y=tel["Y"],
        mode="markers",
        marker=dict(
            size=6,
            color=tel[color_metric],
            colorscale=colorscales.get(color_metric, "Turbo"),
            colorbar=dict(
                title=dict(text=color_metric, font=dict(color="#FFFFFF", size=11)),
                tickfont=dict(color="#A0A4B8"),
                len=0.75,
                thickness=16
            ),
            showscale=True
        ),
        hovertext=[
            f"Distance: {d:.0f}m<br>Speed: {s:.1f} km/h<br>Throttle: {th:.0f}%<br>Brake: {br}<br>Gear: {g}"
            for d, s, th, br, g in zip(tel["Distance"], tel["Speed"], tel["Throttle"], tel["Brake"], tel.get("nGear", [0]*len(tel)))
        ],
        hoverinfo="text",
        name="Racing Line"
    ))

    # Detect apexes and plot corner pins
    apexes = detect_apexes(tel)
    if apexes:
        apex_df = pd.DataFrame(apexes)
        # Find nearest X, Y for apex distances
        apex_coords = []
        for _, ap in apex_df.iterrows():
            closest_idx = (tel["Distance"] - ap["Distance"]).abs().idxmin()
            apex_coords.append({
                "Corner": f"T{ap['Corner']}",
                "X": tel.loc[closest_idx, "X"],
                "Y": tel.loc[closest_idx, "Y"],
                "Speed": ap["ApexSpeed"]
            })
        
        ap_plot_df = pd.DataFrame(apex_coords)
        fig.add_trace(go.Scatter(
            x=ap_plot_df["X"],
            y=ap_plot_df["Y"],
            mode="text+markers",
            text=ap_plot_df["Corner"],
            textposition="top center",
            textfont=dict(color="#FFDF00", size=10, family="Consolas"),
            marker=dict(size=8, color="#FFDF00", symbol="diamond"),
            name="Corner Apex",
            hoverinfo="text",
            hovertext=[f"{c}: {spd} km/h" for c, spd in zip(ap_plot_df["Corner"], ap_plot_df["Speed"])]
        ))

    # Equal aspect ratio for true track representation
    fig.update_layout(
        yaxis=dict(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=620
    )
    apply_f1_plot_theme(fig, title=f"{session_data.get('circuit_name', 'Circuit')} - {driver} Fastest Lap Profile", height=620)
    st.plotly_chart(fig, use_container_width=True)

    # Summary corner speeds
    if apexes:
        st.markdown("#### 🎯 Corner Velocity Breakdown")
        st.dataframe(pd.DataFrame(apexes), use_container_width=True, height=220)
