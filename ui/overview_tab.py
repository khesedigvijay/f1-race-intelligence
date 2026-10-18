"""
Race Overview Tab Component.
Displays event header, key metrics, results classification, and executive summary.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ui.theme import render_metric_card, apply_f1_plot_theme
from utils.formatting import get_team_color

def render_overview_tab(session_data: dict):
    """Renders the Race Overview page tab."""
    event_name = session_data.get("event_name", "Grand Prix")
    circuit_name = session_data.get("circuit_name", "Circuit")
    season = session_data.get("season", 2024)
    session_type = session_data.get("session_type", "Race")
    date = session_data.get("date", "N/A")
    total_laps = session_data.get("total_laps", 0)
    fastest_lap = session_data.get("fastest_lap", "N/A")
    fastest_driver = session_data.get("fastest_driver", "N/A")
    sc_count = session_data.get("safety_cars", 0)
    vsc_count = session_data.get("vsc", 0)
    is_synth = session_data.get("is_synthetic", False)

    # Top badges & Header
    col_hdr, col_badge = st.columns([3, 1])
    with col_hdr:
        st.markdown(f"## {event_name} - {season}")
        st.caption(f"🏁 **{circuit_name}** | {session_type} | Date: {date}")
    with col_badge:
        if is_synth:
            st.markdown('<div style="text-align: right;"><span class="badge-demo">SYNTHETIC DEMO DATA</span></div>', unsafe_allow_html=True)
            st.caption("Offline fallback dataset")
        else:
            st.markdown('<div style="text-align: right;"><span class="badge-live">LIVE FASTF1 DATA</span></div>', unsafe_allow_html=True)
            st.caption("Official timing session")

    # Metric Cards Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric_card("Total Laps", f"{total_laps}", "Scheduled Distance"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric_card("Fastest Lap", f"{fastest_lap}", f"Driver: {fastest_driver}"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric_card("Safety Cars", f"{sc_count}", f"{vsc_count} VSC periods", delta_color="#FF8000"), unsafe_allow_html=True)
    with c4:
        weather_summary = session_data.get("weather", pd.DataFrame())
        avg_temp = f"{weather_summary['TrackTemp'].mean():.1f} °C" if not weather_summary.empty and 'TrackTemp' in weather_summary.columns else "32.0 °C"
        st.markdown(render_metric_card("Track Temp", avg_temp, "Mean Session Temp", delta_color="#E10600"), unsafe_allow_html=True)

    # Classification & Finishing vs Grid Plot
    st.markdown("### 🏆 Final Classification & Grid Progression")
    results = session_data.get("results", pd.DataFrame())
    
    if not results.empty:
        col_table, col_chart = st.columns([1, 1])
        with col_table:
            # Display results table
            display_cols = []
            rename_map = {}
            for col, target in [("pos", "P"), ("Position", "P"), ("code", "Driver"), ("Abbreviation", "Driver"), 
                                ("team", "Constructor"), ("TeamName", "Constructor"), ("grid", "Grid"), ("GridPosition", "Grid"),
                                ("status", "Status")]:
                if col in results.columns and target not in display_cols:
                    display_cols.append(col)
                    rename_map[col] = target

            table_df = results[display_cols].rename(columns=rename_map)
            st.dataframe(table_df, use_container_width=True, height=360)

        with col_chart:
            # Grid vs Finish Position Dumbbell/Slope Plot
            if ("grid" in results.columns or "GridPosition" in results.columns) and ("pos" in results.columns or "Position" in results.columns):
                grid_c = "grid" if "grid" in results.columns else "GridPosition"
                pos_c = "pos" if "pos" in results.columns else "Position"
                driver_c = "code" if "code" in results.columns else ("Abbreviation" if "Abbreviation" in results.columns else "Driver")

                chart_df = results.copy().head(12)
                chart_df["GridNum"] = pd.to_numeric(chart_df[grid_c], errors="coerce").fillna(20)
                chart_df["PosNum"] = pd.to_numeric(chart_df[pos_c], errors="coerce").fillna(20)
                chart_df["NetGain"] = chart_df["GridNum"] - chart_df["PosNum"]
                chart_df["Color"] = chart_df["NetGain"].apply(lambda x: "#00D2BE" if x > 0 else ("#E10600" if x < 0 else "#FFFFFF"))

                fig = go.Figure()
                for _, r in chart_df.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[r["GridNum"], r["PosNum"]],
                        y=[r[driver_c], r[driver_c]],
                        mode="lines+markers",
                        line=dict(color=r["Color"], width=2.5),
                        marker=dict(size=[8, 11], color=["#8E92A8", r["Color"]]),
                        showlegend=False,
                        hoverinfo="text",
                        hovertext=f"Driver: {r[driver_c]}<br>Grid: P{int(r['GridNum'])} -> Finish: P{int(r['PosNum'])}<br>Delta: {int(r['NetGain']):+d}"
                    ))

                fig.update_layout(
                    xaxis_title="Position (Grid to Finish)",
                    yaxis_title="Driver",
                    yaxis=dict(autorange="reversed")
                )
                apply_f1_plot_theme(fig, title="Grid (Grey) to Finish (Colored) Progression", height=360)
                st.plotly_chart(fig, use_container_width=True)
