"""
Machine Learning and Predictive Analytics Tab Component.
Lap-time prediction with time-aware train/test split, feature importance, outlier detection, and model validation.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from models.lap_time_predictor import train_time_aware_lap_predictor
from models.consistency_scorer import detect_pace_outliers
from ui.theme import apply_f1_plot_theme, render_metric_card

def render_ml_tab(session_data: dict):
    """Renders the Machine Learning Predictions tab."""
    st.markdown("### 🤖 Advanced Machine Learning & Predictive Analytics")
    st.caption("Time-aware lap time prediction, feature attribution, and anomaly detection without future data leakage.")

    laps = session_data.get("laps", pd.DataFrame())
    if laps.empty or len(laps) < 30:
        st.warning("Insufficient laps available to train the machine learning pipeline.")
        return

    # Split Slider
    col_split, col_driver = st.columns([1, 1])
    with col_split:
        train_split = st.slider("Chronological Train Cutoff (%)", min_value=0.50, max_value=0.80, value=0.65, step=0.05, help="Train model only on past laps (e.g. Laps 1 to 37) and evaluate on remaining future laps.")
    with col_driver:
        avail_drivers = sorted(laps["Driver"].unique())
        selected_driver = st.selectbox("Inspect Driver Predictions", avail_drivers, index=0)

    # Train Model
    with st.spinner("Training time-aware lap-time regression model..."):
        ml_results = train_time_aware_lap_predictor(laps, train_split_pct=train_split)

    if ml_results.get("status") != "success":
        st.error(f"Model training notice: {ml_results.get('message', 'Failed to train.')}")
        return

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(render_metric_card("Test MAE", f"±{ml_results['mae']:.3f}s", f"RMSE: {ml_results['rmse']:.3f}s"), unsafe_allow_html=True)
    with m2:
        st.markdown(render_metric_card("Test R² Score", f"{ml_results['r2_score']:.3f}", "Generalization Metric"), unsafe_allow_html=True)
    with m3:
        st.markdown(render_metric_card("Cutoff Lap", f"Lap {ml_results['cutoff_lap']}", f"{ml_results['train_samples']} Train Laps"), unsafe_allow_html=True)
    with m4:
        st.markdown(render_metric_card("Holdout Size", f"{ml_results['test_samples']} Laps", "Future Test Set"), unsafe_allow_html=True)

    # Actual vs Predicted Plot
    st.markdown("#### 📉 Test Set: Actual vs. ML Predicted Lap Times")
    comp_df = ml_results.get("full_comparison_df", pd.DataFrame())
    
    if not comp_df.empty:
        driver_test = comp_df[comp_df["Driver"] == selected_driver].sort_values("LapNumber")
        if not driver_test.empty:
            fig_pred = go.Figure()

            fig_pred.add_trace(go.Scatter(
                x=driver_test["LapNumber"],
                y=driver_test["LapTimeSeconds"],
                mode="lines+markers",
                name="Actual Lap Time",
                line=dict(color="#FFFFFF", width=2),
                marker=dict(size=6, color="#00D2BE")
            ))

            fig_pred.add_trace(go.Scatter(
                x=driver_test["LapNumber"],
                y=driver_test["PredictedSeconds"],
                mode="lines+markers",
                name="ML Predicted Pace",
                line=dict(color="#E10600", width=2, dash="dash"),
                marker=dict(size=6, color="#E10600")
            ))

            fig_pred.update_xaxes(title="Race Lap Number (Holdout Test Set)")
            fig_pred.update_yaxes(title="Lap Time (Seconds)")
            apply_f1_plot_theme(fig_pred, title=f"{selected_driver} - Actual vs. Predicted Pace on Test Laps", height=420)
            st.plotly_chart(fig_pred, use_container_width=True)
        else:
            st.info(f"Driver {selected_driver} has no laps in the holdout test set.")

    # Feature Importance & Anomaly Detection
    col_feat, col_outliers = st.columns(2)
    with col_feat:
        st.markdown("#### 🧠 Model Feature Importance")
        importances = ml_results.get("feature_importances", [])
        if importances:
            f_names = [i["feature"] for i in importances]
            f_vals = [i["importance"] for i in importances]
            
            fig_imp = go.Figure()
            fig_imp.add_trace(go.Bar(
                x=f_vals[::-1],
                y=f_names[::-1],
                orientation="h",
                marker=dict(color="#E10600"),
                text=[f"{v:.1f}%" for v in f_vals[::-1]],
                textposition="auto"
            ))
            fig_imp.update_layout(xaxis_title="Relative Attribution (%)", yaxis_title="Feature")
            apply_f1_plot_theme(fig_imp, title="Attribution of Pace Predictors", height=280)
            st.plotly_chart(fig_imp, use_container_width=True)

    with col_outliers:
        st.markdown(f"#### ⚠️ {selected_driver} Anomaly & Outlier Laps")
        driver_all_laps = laps[laps["Driver"] == selected_driver]
        outliers_df = detect_pace_outliers(driver_all_laps)
        if not outliers_df.empty:
            st.dataframe(outliers_df, use_container_width=True, height=280)
        else:
            st.info("No anomalous pace outliers detected for this driver.")

    # Disclaimers & Assumptions
    st.markdown("---")
    st.markdown("#### 📋 Model Governance & Limitations")
    for lim in ml_results.get("limitations", []):
        st.markdown(f"- ℹ️ {lim}")
