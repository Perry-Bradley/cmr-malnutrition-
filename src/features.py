"""Feature engineering helpers (real-data feature set)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ALL_FEATURES, TARGET


def add_engineered(df: pd.DataFrame) -> pd.DataFrame:
    """Add a small set of interaction / composite features."""
    df = df.copy()
    df["wash_composite"] = (df["improved_water_pct"] + df["improved_sanitation_pct"]) / 2
    df["maternal_health_score"] = (
        df["antenatal_4plus_pct"].rank(pct=True)
        + df["skilled_birth_attendance_pct"].rank(pct=True)
        + df["health_facility_delivery_pct"].rank(pct=True)
    ) / 3 * 100  # scale back to 0-100 so it sits with the other percentages
    df["education_score"] = (
        df["women_secondary_plus_pct"] + df["women_literate_pct"]
    ) / 2  # composite maternal education score
    df["disease_burden"] = (df["malaria_prevalence_pct"] + df["child_anemia_pct"]) / 2
    return df


ENGINEERED = [
    "wash_composite",
    "maternal_health_score",
    "education_score",
    "disease_burden",
]


def feature_matrix(df: pd.DataFrame, include_engineered: bool = True):
    """Return (X, y) ready for sklearn."""
    cols = list(ALL_FEATURES)
    if include_engineered:
        df = add_engineered(df)
        cols += ENGINEERED
    return df[cols].copy(), df[TARGET].copy()
