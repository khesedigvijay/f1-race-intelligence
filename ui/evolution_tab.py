"""
Track Evolution Tab Component.
Session-by-session lap time progression, sector improvement, and rubbering-in rates.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from analysis.track_evolution import compute_track_evolution_metrics, estimate_rubber_in_rate
from ui.theme import apply_f1_plot_theme, render_metric_card
from utils.formatting import format_seconds_to_laptime

def render_evolution_tab(session_data: dict):
    """Renders the Track Evolution tab."""
    st.markdown("### 🛣️ Track Evolution & Circuit Progression")
    st.caption("Pace ramp-up across the Grand Prix weekend as rubber is deposited on the racing line.")

    evolution_df = session_data.get("evolution", pd.DataFrame())
    
    if evolution_df.empty or "BestLap" not in evolution_df.columns:
        # Fallback if only single session exists: evaluate within-session evolution
        st.info("Cross-session evolution records unavailable for this single session. Displaying within-session track grip evolution.")
        laps = session_data.get("laps", pd.DataFrame())
        rubber_stats = estimate_rubber_in_rate(laps)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(render_metric_card("Rubbering Rate", f"{rubber_stats.get('slope_sec_per_lap', 0.0):+.3f}s / lap", "Field Pace Slope"), unsafe_allow_html=True)
        with c2:
            st.markdown(render_metric_card("Fit Confidence (R²)", f"{rubber_stats.get('r_squared', 0.0)}", "Field Median Trend"), unsafe_allow_html=True)
        return

    metrics = compute_track_evolution_metrics(evolution_df)

    # Top metric cards
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(render_metric_card("Total Evolution", f"-{metrics['total_evolution_seconds']:.3f}s", f"{metrics['evolution_percentage']}% Pace Gain"), unsafe_allow_html=True)
    with m2:
        st.markdown(render_metric_card("Initial FP1 Pace", format_seconds_to_laptime(metrics['initial_lap']), "Dusty Baseline Track"), unsafe_allow_html=True)
    with m3:
        st.markdown(render_metric_card("Peak Qualifying Lap", format_seconds_to_laptime(metrics['peak_quali_lap']), "Maximum Rubber Grip", delta_color="#E10600"), unsafe_allow_html=True)

    # Progression Chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=evolution_df["Session"],
        y=evolution_df["BestLap"],
        name="Session Best Lap",
        marker=dict(color="#E10600", line=dict(color="#FFFFFF", width=1)),
        text=evolution_df["BestLap"].apply(format_seconds_to_laptime),
        textposition="auto"
    ))

    # Add trend line
    fig.add_trace(go.Scatter(
        x=evolution_df["Session"],
        y=evolution_df["BestLap"],
        mode="lines+markers",
        name="Evolution Trend",
        line=dict(color="#00D2BE", width=2.5),
        marker=dict(size=8, color="#FFFFFF")
    ))

    # Reverse y-axis so faster (lower) lap times are higher
    min_y = evolution_df["BestLap"].min() - 0.8
    max_y = evolution_df["BestLap"].max() + 0.8
    fig.update_layout(yaxis=dict(range=[max_y, min_y], title="Lap Time (Seconds)"))
    fig.update_xaxes(title="Grand Prix Session")
    apply_f1_plot_theme(fig, title="Session-by-Session Lap Time Progression (Faster Laps are Higher)", height=450)
    st.plotly_chart(fig, use_container_width=True)

    # Session Table
    st.markdown("#### 📊 Session Track Conditions and Temperatures")
    st.dataframe(evolution_df, use_container_width=True)

    st.info("ℹ️ **Confounder Awareness:** Peak pace in Qualifying reflects both maximum rubber grip AND low fuel (~5 kg) with softest compound, compared to race sessions carrying ~100 kg fuel loads.")
