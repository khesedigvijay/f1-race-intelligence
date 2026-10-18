"""
Data Explorer, Executive Insights, and Export Tab Component.
Automated racing insights generator and CSV/JSON/Markdown export capabilities.
"""

import streamlit as st
import pandas as pd
from utils.export import convert_df_to_csv, convert_dict_to_json, generate_race_executive_summary
from analysis.tire_degradation import calculate_compound_degradation
from analysis.performance import calculate_sector_dominance, calculate_driver_pace_rankings

def generate_automatic_insights(session_data: dict) -> list:
    """Generates structured racing insights from session data."""
    insights = []
    laps = session_data.get("laps", pd.DataFrame())
    
    if laps.empty:
        return ["No lap data available to compute automated insights."]

    # 1. Fastest Sectors
    sectors = calculate_sector_dominance(laps)
    if not sectors.empty:
        best_s1 = sectors.loc[sectors["BestS1"].idxmin()]
        best_s2 = sectors.loc[sectors["BestS2"].idxmin()]
        best_s3 = sectors.loc[sectors["BestS3"].idxmin()]
        insights.append(f"Sector Dominance: {best_s1['Driver']} set the fastest S1 ({best_s1['BestS1']:.3f}s), {best_s2['Driver']} in S2 ({best_s2['BestS2']:.3f}s), and {best_s3['Driver']} in S3 ({best_s3['BestS3']:.3f}s).")

    # 2. Race Pace Leader
    pace_rank = calculate_driver_pace_rankings(laps)
    if not pace_rank.empty:
        p1 = pace_rank.iloc[0]
        insights.append(f"True Race Pace: {p1['Driver']} recorded the lowest median race pace of {p1['MedianPace']} across {p1['LapsSampled']} clean laps.")

    # 3. Tire Degradation
    deg = calculate_compound_degradation(laps)
    if deg:
        for comp, s in deg.items():
            insights.append(f"Compound Wear: {comp} tires experienced an estimated pace loss of +{s['degradation_rate_sec_per_lap']:.3f}s per lap (R²: {s['r_squared']}).")

    # 4. Neutralizations
    sc = session_data.get("safety_cars", 0)
    vsc = session_data.get("vsc", 0)
    if sc > 0 or vsc > 0:
        insights.append(f"Neutralizations: {sc} full Safety Car and {vsc} Virtual Safety Car periods neutralized racing gaps.")

    return insights

def render_explorer_tab(session_data: dict):
    """Renders the Data Explorer and Insights tab."""
    st.markdown("### 📑 Race Insights, Data Explorer & Reports")
    st.caption("Automatic data-driven takeaways, searchable raw timing tables, and export downloads.")

    # Executive Insights Section
    st.markdown("#### 💡 Automatic Executive Race Insights")
    insights = generate_automatic_insights(session_data)
    for ins in insights:
        st.markdown(f"- 🏁 {ins}")

    st.markdown("---")

    # Export Area
    st.markdown("#### 💾 Export Intelligence & Datasets")
    laps = session_data.get("laps", pd.DataFrame())
    
    col_csv, col_json, col_rep = st.columns(3)
    
    with col_csv:
        if not laps.empty:
            csv_bytes = convert_df_to_csv(laps)
            st.download_button(
                label="📥 Download Laps (CSV)",
                data=csv_bytes,
                file_name=f"{session_data.get('event_name', 'F1')}_{session_data.get('season', 2024)}_laps.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col_json:
        # Prepare lightweight serializable summary dict
        export_summary = {
            "event": session_data.get("event_name"),
            "circuit": session_data.get("circuit_name"),
            "season": session_data.get("season"),
            "session": session_data.get("session_type"),
            "date": session_data.get("date"),
            "fastest_lap": session_data.get("fastest_lap"),
            "fastest_driver": session_data.get("fastest_driver"),
            "insights": insights
        }
        json_str = convert_dict_to_json(export_summary)
        st.download_button(
            label="📥 Download Summary (JSON)",
            data=json_str,
            file_name=f"{session_data.get('event_name', 'F1')}_{session_data.get('season', 2024)}_summary.json",
            mime="application/json",
            use_container_width=True
        )

    with col_rep:
        report_md = generate_race_executive_summary(session_data, insights)
        st.download_button(
            label="📥 Download Executive Report (MD)",
            data=report_md,
            file_name=f"{session_data.get('event_name', 'F1')}_{session_data.get('season', 2024)}_report.md",
            mime="text/markdown",
            use_container_width=True
        )

    st.markdown("---")

    # Raw Interactive Data Explorer
    st.markdown("#### 🔍 Interactive Lap Data Explorer")
    if not laps.empty:
        # Multi-select columns
        all_cols = list(laps.columns)
        default_cols = [c for c in ["Driver", "LapNumber", "LapTimeSeconds", "Compound", "TyreLife", "Stint", "Sector1Seconds", "Sector2Seconds", "Sector3Seconds"] if c in all_cols]
        chosen_cols = st.multiselect("Display Columns", options=all_cols, default=default_cols)
        
        # Filter by driver
        driver_filter = st.multiselect("Filter by Driver", options=sorted(laps["Driver"].unique()), default=[])
        view_df = laps if not driver_filter else laps[laps["Driver"].isin(driver_filter)]

        st.dataframe(view_df[chosen_cols].reset_index(drop=True), use_container_width=True, height=360)
    else:
        st.info("No raw lap records to display.")
