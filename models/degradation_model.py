"""
Tire degradation machine learning regression models with uncertainty intervals.
Includes Linear, Polynomial, and Ridge formulations to estimate wear curves and cliff points.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

def fit_tire_wear_curve(
    tire_ages: np.ndarray, 
    lap_times: np.ndarray, 
    degree: int = 1
) -> Dict[str, Any]:
    """
    Fits tire wear regression with prediction uncertainty standard error.
    """
    if len(tire_ages) < 4:
        return {"status": "insufficient_data"}

    X = tire_ages.reshape(-1, 1)
    y = lap_times

    if degree == 1:
        # Simple Ridge Regression
        model = Ridge(alpha=1.0)
        model.fit(X, y)
        preds = model.predict(X)
        slope = float(model.coef_[0])
        intercept = float(model.intercept_)
    else:
        # Polynomial fit
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        model = Ridge(alpha=1.0)
        model.fit(X_poly, y)
        preds = model.predict(X_poly)
        slope = float(model.coef_[0])
        intercept = float(model.intercept_)

    residuals = y - preds
    variance = np.var(residuals, ddof=2) if len(y) > 2 else 0.01
    std_err = np.sqrt(variance)

    # Calculate R2
    ss_tot = np.sum((y - np.mean(y))**2)
    ss_res = np.sum(residuals**2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Project future wear up to 35 laps
    proj_ages = np.arange(1, 36)
    if degree == 1:
        proj_preds = model.predict(proj_ages.reshape(-1, 1))
    else:
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        proj_preds = model.predict(poly.fit_transform(proj_ages.reshape(-1, 1)))

    return {
        "status": "success",
        "slope_sec_per_lap": round(slope, 4),
        "intercept": round(intercept, 3),
        "r2_score": round(max(0.0, r2), 3),
        "std_error": round(float(std_err), 3),
        "projected_ages": proj_ages.tolist(),
        "projected_lap_times": [round(float(p), 3) for p in proj_preds],
        "ci_upper": [round(float(p + 1.96 * std_err), 3) for p in proj_preds],
        "ci_lower": [round(float(p - 1.96 * std_err), 3) for p in proj_preds],
    }
