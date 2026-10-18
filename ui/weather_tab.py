"""
Weather and Environmental Conditions Tab Component.
Track and air temperature telemetry, humidity, wind conditions, and pace correlation.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from analysis.weather import summarize_weather, correlate_weather_with_pace
from ui.theme import apply_f1_plot_theme, render_metric_card

def render_weather_tab(session_data: dict):
    """Renders the Weather & Track Conditions tab."""
    st.markdown("### 🌤️ Weather & Environmental Telemetry")
    st.caption("Ambient and track temperatures, humidity, wind vectors, and pace correlation.")

    weather_df = session_data.get("weather", pd.DataFrame())
    if weather_df.empty or "TrackTemp" not in weather_df.columns:
        st.warning("Weather telemetry unavailable for this session.")
        return

    summary = summarize_weather(weather_df)

    # Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric_card("Track Temp", f"{summary['track_temp']['mean']} °C", f"Range: {summary['track_temp']['min']}° - {summary['track_temp']['max']}°C", delta_color="#E10600"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric_card("Air Temp", f"{summary['air_temp']['mean']} °C", f"Range: {summary['air_temp']['min']}° - {summary['air_temp']['max']}°C"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric_card("Humidity", f"{summary['humidity']['mean']}%", f"Delta: {summary['humidity']['delta']:+0.1f}%"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_metric_card("Rainfall", "DETECTED" if summary['rainfall_present'] else "NONE", "Track Condition Status", delta_color="#00A3E0" if summary['rainfall_present'] else "#00D2BE"), unsafe_allow_html=True)

    # Temperature Evolution Chart
    fig = go.Figure()
    
    x_axis = weather_df["Time"] if "Time" in weather_df.columns else list(range(len(weather_df)))

    fig.add_trace(go.Scatter(
        x=x_axis,
        y=weather_df["TrackTemp"],
        mode="lines",
        name="Track Temperature (°C)",
        line=dict(color="#E10600", width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=x_axis,
        y=weather_df["AirTemp"],
        mode="lines",
        name="Air Temperature (°C)",
        line=dict(color="#00D2BE", width=2.0)
    ))

    if "Humidity" in weather_df.columns:
        fig.add_trace(go.Scatter(
            x=x_axis,
            y=weather_df["Humidity"],
            mode="lines",
            name="Humidity (%)",
            line=dict(color="#FFDF00", width=1.5, dash="dot"),
            yaxis="y2"
        ))

    fig.update_layout(
        yaxis=dict(title="Temperature (°C)"),
        yaxis2=dict(title="Humidity (%)", overlaying="y", side="right", showgrid=False, tickfont=dict(color="#FFDF00")),
        xaxis=dict(title="Session Time")
    )
    apply_f1_plot_theme(fig, title="Track vs. Air Temperature Dynamics", height=420)
    st.plotly_chart(fig, use_container_width=True)

    # Correlation Analysis
    laps = session_data.get("laps", pd.DataFrame())
    corr_results = correlate_weather_with_pace(weather_df, laps)

    st.markdown("#### 🔬 Track Temperature vs. Field Lap Pace Correlation")
    col_corr, col_caveat = st.columns([1, 2])
    with col_corr:
        st.markdown(render_metric_card("Pearson r", f"{corr_results.get('correlation', 0.0):+.3f}", f"p-value: {corr_results.get('p_value', 1.0):.4f}"), unsafe_allow_html=True)
    with col_caveat:
        st.info(f"**Insight:** {corr_results.get('interpretation', 'N/A')}\n\n**Scientific Caveat:** {corr_results.get('caveat', '')}")
