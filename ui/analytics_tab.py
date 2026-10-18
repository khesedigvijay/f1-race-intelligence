"""
Driver and Team Analytics Tab Component.
Median clean pace rankings, sector dominance, net overtaking/positions gained, and consistency ratings.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from analysis.performance import calculate_driver_pace_rankings, calculate_sector_dominance, calculate_position_changes
from models.consistency_scorer import compute_driver_consistency
from ui.theme import apply_f1_plot_theme, render_metric_card

def render_analytics_tab(session_data: dict):
    """Renders the Driver & Team Performance Analytics tab."""
    st.markdown("### 🏆 Driver & Constructor Performance Intelligence")
    st.caption("Normalized median pace, theoretical sector potentials, overtaking indices, and lap consistency ratings.")

    laps = session_data.get("laps", pd.DataFrame())
    results = session_data.get("results", pd.DataFrame())

    if laps.empty:
        st.warning("Insufficient timing records to compute performance rankings.")
        return

    # 1. Representative Race Pace Rankings
    st.markdown("#### ⏱️ True Race Pace Ranking (Clean Median Lap Time)")
    pace_df = calculate_driver_pace_rankings(laps)
    
    if not pace_df.empty:
        col_rank, col_chart = st.columns([1, 1])
        with col_rank:
            st.dataframe(pace_df[["Driver", "LapsSampled", "MedianPace", "PaceDeltaToP1", "BestLap"]], use_container_width=True, height=320)
        with col_chart:
            # Bar chart of Delta to P1
            fig_pace = go.Figure()
            fig_pace.add_trace(go.Bar(
                x=pace_df["Driver"],
                y=pace_df["DeltaSeconds"],
                marker=dict(color="#E10600", line=dict(color="#FFFFFF", width=1)),
                text=[f"+{d:.3f}s" if d > 0 else "P1 (0.000s)" for d in pace_df["DeltaSeconds"]],
                textposition="auto"
            ))
            fig_pace.update_layout(xaxis_title="Driver", yaxis_title="Pace Gap to Fastest Median (s)")
            apply_f1_plot_theme(fig_pace, title="Pace Gap to Fastest Median (s)", height=320)
            st.plotly_chart(fig_pace, use_container_width=True)

    # 2. Consistency Scores
    st.markdown("#### 🎯 Driver Consistency Ratings (Low Lap-to-Lap Variance)")
    cons_df = compute_driver_consistency(laps)
    if not cons_df.empty:
        st.dataframe(cons_df[["Driver", "ConsistencyScore", "Rating", "MeanLapSec", "StdDevSec", "CV_Pct"]], use_container_width=True, height=240)

    # 3. Sector Dominance & Theoretical Best Laps
    st.markdown("#### 🚀 Sector Dominance & Theoretical Ideal Laps")
    sector_df = calculate_sector_dominance(laps)
    if not sector_df.empty:
        st.dataframe(sector_df, use_container_width=True, height=260)

    # 4. Net Positions Gained/Lost
    if not results.empty:
        st.markdown("#### 🔀 Positions Gained / Lost from Starting Grid")
        pos_df = calculate_position_changes(results)
        if not pos_df.empty:
            fig_pos = go.Figure()
            colors = ["#00D2BE" if p > 0 else ("#E10600" if p < 0 else "#8E92A8") for p in pos_df["PositionsGained"]]
            fig_pos.add_trace(go.Bar(
                x=pos_df["DriverCode"],
                y=pos_df["PositionsGained"],
                marker=dict(color=colors),
                text=[f"{p:+d}" for p in pos_df["PositionsGained"]],
                textposition="auto"
            ))
            fig_pos.update_layout(xaxis_title="Driver", yaxis_title="Net Positions Gained")
            apply_f1_plot_theme(fig_pos, title="Net Grid Positions Gained / Lost", height=320)
            st.plotly_chart(fig_pos, use_container_width=True)
