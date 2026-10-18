"""
Tire Degradation and Wear Analytics Tab Component.
Compound wear curves, fuel burn compensation, stint delta comparisons, and confidence intervals.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from analysis.tire_degradation import (
    calculate_compound_degradation, 
    get_stint_breakdown, 
    filter_clean_racing_laps, 
    apply_fuel_correction
)
from ui.theme import apply_f1_plot_theme, render_metric_card
from utils.formatting import get_compound_color

def render_tire_tab(session_data: dict):
    """Renders the Tire Degradation analysis tab."""
    st.markdown("### 🛞 Compound Degradation & Stint Pace Analytics")
    st.caption("Pace loss modeling per lap with fuel-burn compensation, outlier filtering, and 95% statistical confidence intervals.")

    laps = session_data.get("laps", pd.DataFrame())
    if laps.empty or "LapTimeSeconds" not in laps.columns:
        st.warning("No lap data available to compute tire wear.")
        return

    # Configuration controls
    col_fc, col_fuel_val = st.columns([1, 1])
    with col_fc:
        use_fuel_corr = st.toggle("Apply Fuel-Burn Pace Correction", value=True, help="Removes the ~0.05s/lap natural car speedup as fuel burns off to isolate pure rubber degradation.")
    with col_fuel_val:
        fuel_rate = st.slider("Fuel Effect (seconds gained per lap)", min_value=0.020, max_value=0.080, value=0.050, step=0.005, disabled=not use_fuel_corr)

    # Compute degradation stats
    deg_stats = calculate_compound_degradation(laps, use_fuel_correction=use_fuel_corr, fuel_effect_per_lap=fuel_rate)

    if not deg_stats:
        st.info("Insufficient clean laps across compounds to isolate degradation curves.")
        return

    # Metric cards for compound wear rates
    cols = st.columns(len(deg_stats))
    for idx, (comp, stats) in enumerate(deg_stats.items()):
        with cols[idx]:
            rate = stats["degradation_rate_sec_per_lap"]
            ci = stats["ci_95"]
            color = get_compound_color(comp)
            st.markdown(
                f"""
                <div class="f1-card" style="border-top-color: {color};">
                    <div class="f1-card-label">{comp} DEGRADATION</div>
                    <div class="f1-card-value">+{rate:.3f}s <span style="font-size: 0.9rem; color: #8C90A4;">/ lap</span></div>
                    <div class="f1-card-sub" style="color: {color};">95% CI: [{ci[0]:.3f}s, {ci[1]:.3f}s] (R²: {stats['r_squared']})</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Scatter & Regression Fit Plot
    st.markdown("#### 📈 Lap Time vs. Tire Age (Laps Completed on Set)")
    fig = go.Figure()
    
    clean_laps = filter_clean_racing_laps(laps)
    if use_fuel_corr:
        clean_laps = apply_fuel_correction(clean_laps, fuel_effect_per_lap=fuel_rate)
        y_col = "CorrectedLapTimeSeconds"
        y_title = "Fuel-Corrected Lap Time (s)"
    else:
        y_col = "LapTimeSeconds"
        y_title = "Observed Lap Time (s)"

    for comp, stats in deg_stats.items():
        comp_color = get_compound_color(comp)
        sub = clean_laps[clean_laps["Compound"] == comp]
        
        # Raw scatter points
        fig.add_trace(go.Scatter(
            x=sub["TyreLife"],
            y=sub[y_col],
            mode="markers",
            name=f"{comp} Laps (n={len(sub)})",
            marker=dict(color=comp_color, size=6, opacity=0.45),
            hovertext=sub["Driver"] + " - Lap " + sub["LapNumber"].astype(str),
            hoverinfo="text+x+y"
        ))

        # Regression trend line
        x_trend = np.linspace(sub["TyreLife"].min(), sub["TyreLife"].max(), 40)
        slope = stats["degradation_rate_sec_per_lap"]
        base_pace = stats["base_pace_seconds"]
        y_trend = base_pace + slope * x_trend

        fig.add_trace(go.Scatter(
            x=x_trend,
            y=y_trend,
            mode="lines",
            name=f"{comp} Trend (+{slope:.3f}s/lap)",
            line=dict(color=comp_color, width=3)
        ))

    fig.update_xaxes(title_text="Tire Age (Laps on Set)")
    fig.update_yaxes(title_text=y_title)
    apply_f1_plot_theme(fig, title="", height=480)
    st.plotly_chart(fig, use_container_width=True)

    # Stint Breakdown Table
    st.markdown("### 📋 Stint Breakdown & Performance Loss")
    stints_df = get_stint_breakdown(laps)
    if not stints_df.empty:
        st.dataframe(stints_df, use_container_width=True, height=280)
    else:
        st.info("No multi-lap stints available for breakdown.")

    st.caption("⚠️ *Model estimates assume clean racing conditions. Laps affected by traffic, engine saving, or yellow flags are robustly filtered using median MAD thresholds.*")
