"""Train compact linear models and export to JSON for client-side inference.

The website's What-If Predictor needs to run a model in the browser. Tree
ensembles are too heavy to ship; instead we train a standardised Linear
Regression for stunting and a standardised Logistic Regression for the WHO
risk band, plus a K-Means with fitted centroids for cluster assignment.

Output: web/public/data/predictor.json -- everything the browser needs.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .classification import add_risk_band
from .config import OUTPUTS_DIR, RISK_BAND_LABELS
from .features import feature_matrix
from .preprocessing import latest_year


def _export_linreg(X: pd.DataFrame, y: pd.Series) -> dict:
    """Train standardised linear regression, return JSON-safe coefficients."""
    pipe = Pipeline([("scale", StandardScaler()),
                      ("model", LinearRegression())]).fit(X, y)
    scaler: StandardScaler = pipe.named_steps["scale"]
    model: LinearRegression = pipe.named_steps["model"]
    return {
        "features":  list(X.columns),
        "scaler_mean":  scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "coef":      model.coef_.tolist(),
        "intercept": float(model.intercept_),
        "target_min": float(y.min()),
        "target_max": float(y.max()),
    }


def _export_logreg(X: pd.DataFrame, y: pd.Series) -> dict:
    """Train standardised multinomial logistic regression."""
    pipe = Pipeline([("scale", StandardScaler()),
                      ("model", LogisticRegression(max_iter=2000,
                                                    random_state=42))]).fit(X, y)
    scaler: StandardScaler = pipe.named_steps["scale"]
    model: LogisticRegression = pipe.named_steps["model"]
    return {
        "features":     list(X.columns),
        "scaler_mean":  scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "classes":      [str(c) for c in model.classes_],
        "coef":         model.coef_.tolist(),
        "intercept":    model.intercept_.tolist(),
    }


def _export_kmeans(X: pd.DataFrame, k: int = 2) -> dict:
    """Standardised K-Means with centroids in standardised space."""
    scaler = StandardScaler().fit(X)
    km = KMeans(n_clusters=k, n_init=20, random_state=42).fit(scaler.transform(X))
    return {
        "features":     list(X.columns),
        "scaler_mean":  scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "centroids":    km.cluster_centers_.tolist(),
    }


def build_payload(df: pd.DataFrame) -> dict:
    """Train all three deployable models on the full table + return JSON."""
    X, y = feature_matrix(df)
    df_band = add_risk_band(df)
    Xc, _ = feature_matrix(df_band)
    yc = df_band["risk_band"].astype(str)

    # Use the *latest year* slice for K-Means so clusters reflect today's profile.
    latest = latest_year(df)
    Xl, _ = feature_matrix(latest)

    feature_ranges = {
        c: {
            "min":     float(df[c].min())  if c in df.columns else float(X[c].min()),
            "max":     float(df[c].max())  if c in df.columns else float(X[c].max()),
            "median":  float(df[c].median()) if c in df.columns else float(X[c].median()),
        }
        for c in X.columns
    }

    return {
        "regression":      _export_linreg(X, y),
        "classification":  _export_logreg(Xc, yc),
        "clustering":      _export_kmeans(Xl, k=2),
        "risk_bands":      RISK_BAND_LABELS,
        "feature_ranges":  feature_ranges,
    }


def write_payload(df: pd.DataFrame,
                   path: Path = OUTPUTS_DIR / "predictor.json") -> Path:
    payload = build_payload(df)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
