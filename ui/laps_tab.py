"""
Lap-by-Lap Race Progression & Driver Comparison Component.
Interactive filtering by driver, lap range, stint, compound, plus sector-by-sector delta analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ui.theme import apply_f1_plot_theme, render_metric_card
from utils.formatting import get_compound_color, format_seconds_to_laptime

def render_laps_tab(session_data: dict):
    """Renders the Lap-by-Lap Race Comparison tab."""
    st.markdown("### ⏱️ Lap-by-Lap Race Pace & Progression")
    st.caption("Compare stint evolution, lap consistency, pit transitions, and personal best laps.")

    laps = session_data.get("laps", pd.DataFrame())
    if laps.empty or "LapTimeSeconds" not in laps.columns:
        st.warning("No lap data available for progression analysis.")
        return

    available_drivers = sorted(laps["Driver"].unique())
    
    # Filter Row
    col_drivers, col_comp, col_range = st.columns([2, 1, 2])
    with col_drivers:
        selected_drivers = st.multiselect(
            "Select Drivers to Compare",
            options=available_drivers,
            default=available_drivers[:2] if len(available_drivers) >= 2 else available_drivers
        )
    with col_comp:
        all_compounds = sorted([str(c) for c in laps["Compound"].dropna().unique()])
        selected_compounds = st.multiselect("Tire Compound", options=all_compounds, default=all_compounds)
    with col_range:
        min_l = int(laps["LapNumber"].min())
        max_l = int(laps["LapNumber"].max())
        lap_range = st.slider("Lap Range", min_value=min_l, max_value=max_l, value=(min_l, max_l))

    if not selected_drivers:
        st.warning("Please select at least one driver.")
        return

    # Filter DataFrame
    filtered = laps[
        (laps["Driver"].isin(selected_drivers)) &
        (laps["Compound"].astype(str).isin(selected_compounds)) &
        (laps["LapNumber"] >= lap_range[0]) &
        (laps["LapNumber"] <= lap_range[1])
    ].copy()

    if filtered.empty:
        st.info("No laps match the selected criteria.")
        return

    # Primary Lap Progression Chart
    fig = go.Figure()

    driver_palette = ["#00D2BE", "#E10600", "#FF8000", "#3671C6", "#FFFFFF", "#229971"]

    for idx, driver in enumerate(selected_drivers):
        sub = filtered[filtered["Driver"] == driver].sort_values("LapNumber")
        if sub.empty:
            continue

        color = driver_palette[idx % len(driver_palette)]
        
        # Line trace
        fig.add_trace(go.Scatter(
            x=sub["LapNumber"],
            y=sub["LapTimeSeconds"],
            mode="lines+markers",
            name=f"{driver}",
            line=dict(color=color, width=2.2),
            marker=dict(
                size=7,
                color=[get_compound_color(str(c)) for c in sub["Compound"]],
                line=dict(color="#12131C", width=1)
            ),
            hovertext=[
                f"Driver: {driver}<br>Lap: {row['LapNumber']}<br>Time: {format_seconds_to_laptime(row['LapTimeSeconds'])}<br>Compound: {row.get('Compound', 'N/A')}<br>Tire Age: {row.get('TyreLife', 'N/A')} laps"
                for _, row in sub.iterrows()
            ],
            hoverinfo="text"
        ))

        # Highlight driver personal best
        best_lap = sub.loc[sub["LapTimeSeconds"].idxmin()]
        fig.add_trace(go.Scatter(
            x=[best_lap["LapNumber"]],
            y=[best_lap["LapTimeSeconds"]],
            mode="markers",
            name=f"{driver} PB ({format_seconds_to_laptime(best_lap['LapTimeSeconds'])})",
            marker=dict(symbol="star", size=14, color="#FFDF00", line=dict(color="#000000", width=1)),
            showlegend=True
        ))

    fig.update_xaxes(title="Lap Number")
    fig.update_yaxes(title="Lap Time (Seconds)")
    apply_f1_plot_theme(fig, title="Race Pace Evolution & Pit Transitions", height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Sector Breakdown Comparison
    st.markdown("### ⏱️ Sector-by-Sector Comparison")
    sec_cols = ["Driver", "LapNumber", "Compound", "Sector1Seconds", "Sector2Seconds", "Sector3Seconds", "LapTimeSeconds"]
    avail_sec_cols = [c for c in sec_cols if c in filtered.columns]
    
    st.dataframe(filtered[avail_sec_cols].sort_values(["LapNumber", "Driver"]), use_container_width=True, height=300)
