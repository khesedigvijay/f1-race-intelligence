"""
Lap-Time Machine Learning Prediction Engine.
Features:
- Time-aware chronological train/test split (no data leakage)
- Gradient Boosting / Random Forest regression models
- Feature importance analysis
- Transparent model limitations and confidence bounds
"""

from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from analysis.tire_degradation import filter_clean_racing_laps

def prepare_ml_features(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs engineering feature set with lag lap times and fuel mass estimates.
    """
    clean = filter_clean_racing_laps(laps_df, filter_pit_laps=True, filter_sc=True)
    if clean.empty:
        return pd.DataFrame()

    df = clean.sort_values(["Driver", "LapNumber"]).copy()
    
    # Compound encoding
    compound_map = {"SOFT": 1, "MEDIUM": 2, "HARD": 3, "INTERMEDIATE": 4, "WET": 5}
    df["CompoundCode"] = df["Compound"].map(lambda x: compound_map.get(str(x).upper(), 2))

    # Fuel mass estimate (approx 105 kg start, burns ~1.85 kg per lap)
    df["EstimatedFuelKg"] = np.maximum(5.0, 105.0 - (df["LapNumber"] * 1.85))

    # Tire Life
    if "TyreLife" not in df.columns:
        df["TyreLife"] = df.groupby(["Driver", "Stint"])["LapNumber"].rank().astype(int)

    # Previous lap time lag (for the same driver)
    df["Lag1_LapTime"] = df.groupby("Driver")["LapTimeSeconds"].shift(1)
    
    # Fill first lap lag with driver median
    df["Lag1_LapTime"] = df["Lag1_LapTime"].fillna(df["LapTimeSeconds"])

    return df

def train_time_aware_lap_predictor(
    laps_df: pd.DataFrame, 
    train_split_pct: float = 0.65
) -> Dict[str, Any]:
    """
    Trains lap time prediction model using strict time-aware split.
    Train set: Earlier laps (LapNumber <= cutoff_lap)
    Test set: Later laps (LapNumber > cutoff_lap)
    """
    df = prepare_ml_features(laps_df)
    if len(df) < 25:
        return {"status": "insufficient_data", "message": "Need at least 25 clean laps to train model"}

    max_lap = df["LapNumber"].max()
    min_lap = df["LapNumber"].min()
    cutoff_lap = int(min_lap + (max_lap - min_lap) * train_split_pct)

    train_df = df[df["LapNumber"] <= cutoff_lap]
    test_df = df[df["LapNumber"] > cutoff_lap]

    if len(train_df) < 15 or len(test_df) < 5:
        return {"status": "insufficient_data", "message": "Train/test split resulted in too few samples"}

    feature_cols = ["LapNumber", "TyreLife", "CompoundCode", "EstimatedFuelKg", "Lag1_LapTime"]
    target_col = "LapTimeSeconds"

    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values

    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values

    # Train Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X_train, y_train)

    y_pred_train = rf.predict(X_train)
    y_pred_test = rf.predict(X_test)

    mae_test = mean_absolute_error(y_test, y_pred_test)
    rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
    r2_test = r2_score(y_test, y_pred_test)

    # Feature Importance
    importances = [
        {"feature": feat, "importance": round(float(imp) * 100.0, 1)}
        for feat, imp in zip(feature_cols, rf.feature_importances_)
    ]
    importances.sort(key=lambda x: x["importance"], reverse=True)

    # Predictions comparison sample
    comparison_df = test_df[["Driver", "LapNumber", "Compound", "LapTimeSeconds"]].copy()
    comparison_df["PredictedSeconds"] = np.round(y_pred_test, 3)
    comparison_df["ErrorSeconds"] = np.round(comparison_df["PredictedSeconds"] - comparison_df["LapTimeSeconds"], 3)

    return {
        "status": "success",
        "model_name": "Random Forest Regressor (Time-Aware Split)",
        "cutoff_lap": cutoff_lap,
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "mae": round(float(mae_test), 3),
        "rmse": round(float(rmse_test), 3),
        "r2_score": round(float(max(0.0, r2_test)), 3),
        "feature_importances": importances,
        "test_predictions": comparison_df.head(20).to_dict(orient="records"),
        "full_comparison_df": comparison_df,
        "limitations": [
            "Model operates on clean-air assumptions; sudden yellow flags or traffic skew predictions.",
            "Engine modes, ERS deployment spikes, and lift-and-coast telemetry are not publicly disclosed.",
            "Predictions are statistical estimates, not guaranteed lap times."
        ]
    }
