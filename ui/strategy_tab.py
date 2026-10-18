"""
Race Strategy and Pit Stop Simulation Tab Component.
Compound stint Gantt charts, pit sequence logs, undercut/overcut detection, and multi-scenario strategy simulator.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from analysis.race_strategy import extract_pit_stops, evaluate_undercut_potential, simulate_strategy_scenario
from ui.theme import apply_f1_plot_theme, render_metric_card
from utils.formatting import get_compound_color

def render_strategy_tab(session_data: dict):
    """Renders the Race Strategy & Pit Stop Simulator tab."""
    st.markdown("### 🛑 Race Strategy & Pit Stop Analytics")
    st.caption("Stint lifecycle analysis, undercut execution windows, and predictive 1-stop vs 2-stop scenario simulations.")

    laps = session_data.get("laps", pd.DataFrame())
    if laps.empty:
        st.warning("No lap or stint records available for strategy analysis.")
        return

    # 1. Stint Strategy Gantt Chart
    st.markdown("#### 🏎️ Observed Driver Stint Sequences")
    clean_laps = laps.dropna(subset=["LapNumber", "Driver"]).sort_values(["Driver", "LapNumber"])
    
    stint_summary = []
    for (driver, stint), grp in clean_laps.groupby(["Driver", "Stint"]):
        comp = str(grp["Compound"].iloc[0]) if "Compound" in grp.columns else "UNKNOWN"
        start_lap = grp["LapNumber"].min()
        end_lap = grp["LapNumber"].max()
        stint_len = end_lap - start_lap + 1
        stint_summary.append({
            "Driver": driver,
            "Stint": stint,
            "Compound": comp,
            "Start": start_lap,
            "End": end_lap,
            "Length": stint_len
        })

    if stint_summary:
        st_df = pd.DataFrame(stint_summary)
        drivers_list = sorted(st_df["Driver"].unique())
        
        fig_stints = go.Figure()
        for _, row in st_df.iterrows():
            comp_color = get_compound_color(row["Compound"])
            fig_stints.add_trace(go.Bar(
                y=[row["Driver"]],
                x=[row["Length"]],
                base=[row["Start"] - 1],
                orientation="h",
                name=row["Compound"],
                marker=dict(color=comp_color, line=dict(color="#12131C", width=1.5)),
                hovertext=f"Driver: {row['Driver']}<br>Stint: {row['Stint']}<br>Compound: {row['Compound']}<br>Laps: {row['Start']} to {row['End']} ({row['Length']} laps)",
                hoverinfo="text",
                showlegend=False
            ))

        fig_stints.update_layout(
            barmode="stack",
            xaxis_title="Race Lap Number",
            yaxis=dict(title="Driver", categoryorder="array", categoryarray=drivers_list[::-1]),
            height=360
        )
        apply_f1_plot_theme(fig_stints, title="", height=360)
        st.plotly_chart(fig_stints, use_container_width=True)

    # 2. Pit Stop Log & Undercut Analysis
    col_pits, col_undercut = st.columns(2)
    with col_pits:
        st.markdown("#### ⛽ Pit Stop Execution Log")
        pits_df = extract_pit_stops(laps)
        if not pits_df.empty:
            st.dataframe(pits_df, use_container_width=True, height=260)
        else:
            st.info("No discrete pit stops detected in session telemetry.")

    with col_undercut:
        st.markdown("#### ⚡ Undercut Windows Detected")
        undercuts = evaluate_undercut_potential(laps)
        if undercuts:
            st.dataframe(pd.DataFrame(undercuts), use_container_width=True, height=260)
        else:
            st.info("No simultaneous 1-3 lap pit delta battles detected.")

    st.markdown("---")

    # 3. Strategy Scenario Simulator
    st.markdown("### 🔮 Alternative Strategy Scenario Simulator")
    st.caption("Explore optimal race delta between 1-stop and 2-stop tire strategies using empirical pace & degradation models.")

    c_stops, c_loss, c_base = st.columns(3)
    with c_stops:
        tot_laps = st.number_input("Total Race Distance (Laps)", min_value=30, max_value=78, value=int(session_data.get("total_laps", 57)))
    with c_loss:
        pit_delta = st.slider("Pit Lane Loss Delta (s)", min_value=18.0, max_value=30.0, value=23.0, step=0.5, help="Time lost traversing the pit lane and stationary stop compared to flying lap.")
    with c_base:
        base_lap = st.number_input("Hard Baseline Pace (s)", min_value=60.0, max_value=120.0, value=93.5, step=0.5)

    sim = simulate_strategy_scenario(total_laps=tot_laps, pit_loss=pit_delta, base_hard_lap=base_lap)

    st.markdown(f"**Optimal Projected Strategy:** `{sim['optimal_strategy']}`")

    # Cumulative Race Time Curve
    fig_sim = go.Figure()
    sim_colors = ["#00D2BE", "#FF8000", "#E10600", "#FFDF00"]

    for idx, sc in enumerate(sim["scenarios"]):
        color = sim_colors[idx % len(sim_colors)]
        delta_label = f" (Baseline: {sc['formatted_total_time']})" if sc["delta_to_optimal"] == 0 else f" (+{sc['delta_to_optimal']}s)"
        fig_sim.add_trace(go.Scatter(
            x=list(range(1, tot_laps + 1)),
            y=sc["cumulative_times"],
            mode="lines",
            name=f"{sc['name']}{delta_label}",
            line=dict(color=color, width=2.5)
        ))

    fig_sim.update_xaxes(title="Lap Number")
    fig_sim.update_yaxes(title="Cumulative Race Time (Seconds)")
    apply_f1_plot_theme(fig_sim, title="Cumulative Race Time Progression (Lower is Faster)", height=420)
    st.plotly_chart(fig_sim, use_container_width=True)

    # Scenarios Table
    table_rows = []
    for sc in sim["scenarios"]:
        table_rows.append({
            "Strategy Name": sc["name"],
            "Pit Stops": sc["stops"],
            "Total Time": sc["formatted_total_time"],
            "Delta to Optimal": f"+{sc['delta_to_optimal']:.2f}s" if sc["delta_to_optimal"] > 0 else "FASTEST (0.00s)"
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
    st.caption("⚠️ *Simulations are mathematical estimations incorporating fuel mass compensation and compound offsets. Team live strategy accounts for traffic windows, dirty air, and safety car likelihood.*")
