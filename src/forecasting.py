"""Per-sub-region linear forecasts of stunting.

For each sub-region we fit a simple linear time-trend on its observed stunting
values across survey years and extrapolate to ``FORECAST_YEARS`` (2026, 2028).
A linear model is appropriate here because the per-sub-region series only has
a handful of points -- anything more flexible would overfit. The trend slope
itself is a useful indicator: sub-regions improving fastest vs slowest.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from .config import FORECAST_YEARS, TARGET


def fit_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Fit a linear trend per sub-region. Return slope + intercept + r2."""
    rows = []
    for (region, sub), g in df.groupby(["region", "subregion"]):
        if len(g) < 2:
            continue
        X = g["year"].values.reshape(-1, 1)
        y = g[TARGET].values
        m = LinearRegression().fit(X, y)
        rows.append({
            "region": region,
            "subregion": sub,
            "slope_pp_per_year": float(m.coef_[0]),
            "intercept":         float(m.intercept_),
            "r2":                float(m.score(X, y)),
            "last_observed":     float(g.sort_values("year").iloc[-1][TARGET]),
            "last_year":         int(g["year"].max()),
        })
    return pd.DataFrame(rows)


def forecast(df: pd.DataFrame, years: list[int] | None = None) -> pd.DataFrame:
    """Return a long-format dataframe with one row per (sub-region, future-year)."""
    years = years or FORECAST_YEARS
    trends = fit_trends(df)
    out = []
    for _, t in trends.iterrows():
        for y in years:
            pred = t["intercept"] + t["slope_pp_per_year"] * y
            out.append({
                "region":    t["region"],
                "subregion": t["subregion"],
                "year":      int(y),
                "forecast_stunting":  float(np.clip(pred, 0, 100)),
                "slope_pp_per_year":  t["slope_pp_per_year"],
                "trend_r2":           t["r2"],
            })
    return pd.DataFrame(out)


def rank_improvers(trends: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Sub-regions improving the fastest (most-negative slope)."""
    return (trends.sort_values("slope_pp_per_year").head(top_n)
                  .reset_index(drop=True))


def rank_stagnant(trends: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Sub-regions improving the slowest / getting worse (most-positive slope)."""
    return (trends.sort_values("slope_pp_per_year", ascending=False).head(top_n)
                  .reset_index(drop=True))
