"""Build the analysis-ready Cameroon table from the public DHS Program API.

Each row is one *sub-population* of Cameroon defined by the triple
``(SurveyYear, breakdown_dim, breakdown_value)`` -- e.g.

    (2018, "Region", "Far North")
    (2018, "Wealth quintile", "Lowest")
    (2018, "Education", "No education")
    (2018, "Residence", "Urban")
    (2011, "Sex", "Female")

The wide table built from the API contains every indicator value DHS publishes
for each such sub-population. This expands the sample from ~50 (regions only)
to several hundred real DHS observations.

The final analysis table is a *hybrid*: all real DHS API rows are kept intact
and labelled ``data_source="real_dhs"``, then synthetic department-level rows
(``data_source="synthetic"``) are appended to reach HYBRID_TARGET total rows.
"""
from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

from .config import ALL_FEATURES, CAMEROON_REGIONS, PROCESSED_DIR, TARGET
from .dhs_api import fetch_all, to_wide

# Target total rows for the hybrid dataset (real + synthetic).
HYBRID_TARGET = 1040

# Synthetic years: DHS anchor years + evenly-spaced interpolated years
# 15 years × 58 departments = 870 synthetic rows; we sample down to exactly
# (HYBRID_TARGET - n_real) rows so the combined total hits HYBRID_TARGET.
_SYNTH_YEARS = [
    1985, 1988, 1991, 1994, 1998, 2001, 2004,
    2007, 2011, 2014, 2018, 2021, 2024, 2027, 2030,
]

# Synthetic column names → real schema names
_SYNTH_RENAME = {
    "antenatal_visits_4plus_pct":   "antenatal_4plus_pct",
    "health_insurance_coverage_pct": "health_insurance_any_pct",
    "anemia_under5_pct":            "child_anemia_pct",
}

log = logging.getLogger(__name__)

ANALYSIS_TABLE = PROCESSED_DIR / "cameroon_subregional.csv"


# ---- region-name normalisation ----------------------------------------------

# DHS publishes region rows with a leading ".." for sub-region depth and uses
# French names + 1991/1998 mega-regions. Map them all to canonical region names.
_REGION_CANON: dict[str, str] = {
    "Adamaoua": "Adamawa", "Adamawa": "Adamawa",
    "Centre": "Centre",  "Yaounde": "Centre",  "Yaound": "Centre",
    "Est": "East", "East": "East",
    "Extreme-Nord": "Far North", "Extrme-Nord": "Far North", "Far North": "Far North",
    "Littoral": "Littoral", "Douala": "Littoral",
    "Nord": "North", "North": "North",
    "Nord Ouest": "Northwest", "North-West": "Northwest", "Northwest": "Northwest",
    "Sud": "South", "South": "South",
    "Sud Ouest": "Southwest", "South-West": "Southwest", "Southwest": "Southwest",
    "Ouest": "West", "West": "West",
}

# 1991/1998 mega-region rows; we explode them to their constituent regions.
_MEGA: dict[str, list[str]] = {
    "Adamaoua/Nord/Extreme-Nord":  ["Adamawa", "North", "Far North"],
    "Centre/Sud/Est":              ["Centre", "South", "East"],
    "Nord Ouest/Sud Ouest":        ["Northwest", "Southwest"],
    "Ouest/Littoral":              ["West", "Littoral"],
    "Yaounde/Douala":              ["Centre", "Littoral"],
}


def _clean_label(s: str) -> str:
    s = re.sub(r"^\.+\s*", "", str(s).strip())
    s = (s.replace("Adamaoua/Nord/Extr\xeame-Nord", "Adamaoua/Nord/Extreme-Nord")
           .replace("Extr\xeame-Nord", "Extreme-Nord")
           .replace("Yaound\xe9", "Yaounde"))
    return s


def _explode_region_row(row: pd.Series) -> list[pd.Series]:
    """For region rows: split mega-regions to constituents, normalise modern."""
    label = _clean_label(row["breakdown_value"])
    canon = _REGION_CANON.get(label)
    if canon:
        out = row.copy(); out["breakdown_value"] = canon; out["region"] = canon
        return [out]
    if label in _MEGA:
        rows = []
        for r in _MEGA[label]:
            o = row.copy(); o["breakdown_value"] = r; o["region"] = r
            rows.append(o)
        return rows
    return []   # unknown label -> drop


def _build_real() -> pd.DataFrame:
    """Pull and clean the real DHS API rows (~220 rows)."""
    raw = fetch_all()
    wide = to_wide(raw)
    log.info("api wide table: %d rows x %d cols", *wide.shape)

    region_rows = wide[wide["breakdown_dim"] == "Region"]
    exploded: list[pd.Series] = []
    for _, row in region_rows.iterrows():
        exploded.extend(_explode_region_row(row))
    region_df = (pd.DataFrame(exploded) if exploded
                  else region_rows.iloc[0:0].assign(region=pd.Series(dtype=str)))
    if len(region_df):
        agg_cols = [c for c in region_df.columns
                    if c not in ("year", "breakdown_dim", "breakdown_value", "region")]
        region_df = (region_df.groupby(["year", "region"], as_index=False)[agg_cols]
                              .mean()
                              .assign(breakdown_dim="Region"))
        region_df["breakdown_value"] = region_df["region"]

    other = wide[wide["breakdown_dim"] != "Region"].copy()
    other["region"] = "Cameroon"
    skip = {"Total", "Total 15-49"}
    other = other[~other["breakdown_dim"].isin(skip)]

    df = pd.concat([region_df, other], ignore_index=True, sort=False)
    df["subregion"] = df["breakdown_value"].astype(str)
    df = clean(df)
    df["data_source"] = "real_dhs"
    return df


def _build_synthetic_supplement(n: int, seed: int = 42) -> pd.DataFrame:
    """Generate *n* synthetic department-level rows to pad the hybrid table."""
    from .synthetic import build_dataset

    synth = build_dataset(seed=seed, years=_SYNTH_YEARS)  # 870 rows
    synth = synth.sample(n=n, random_state=seed).reset_index(drop=True)

    synth = synth.rename(columns=_SYNTH_RENAME)

    synth["breakdown_dim"]   = "Department"
    synth["breakdown_value"] = synth["subregion"]
    synth["data_source"]     = "synthetic"
    return synth


def load_or_build() -> pd.DataFrame:
    """Return the hybrid analysis table (real DHS + synthetic, cached after first build)."""
    if ANALYSIS_TABLE.exists():
        return pd.read_csv(ANALYSIS_TABLE)

    df_real = _build_real()
    log.info("real DHS rows: %d", len(df_real))

    n_synth = HYBRID_TARGET - len(df_real)
    df_synth = _build_synthetic_supplement(n_synth)
    log.info("synthetic supplement rows: %d", len(df_synth))

    # Align columns: add any column missing from either side as NaN
    all_cols = list(dict.fromkeys(list(df_real.columns) + list(df_synth.columns)))
    for col in all_cols:
        if col not in df_real.columns:
            df_real[col] = np.nan
        if col not in df_synth.columns:
            df_synth[col] = np.nan

    df = pd.concat([df_real[all_cols], df_synth[all_cols]],
                   ignore_index=True, sort=False)

    # Fill remaining NaN in feature columns (synthetic rows missing real-only cols)
    for col in ALL_FEATURES:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())

    ANALYSIS_TABLE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ANALYSIS_TABLE, index=False)
    log.info("hybrid analysis table: %d rows x %d cols", *df.shape)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Type-cast, dedupe, impute, clip.

    Importantly: any row where ``stunting_rate`` was originally NaN is dropped
    BEFORE imputation -- those are sub-populations that DHS did not measure
    stunting for (e.g. MIS 2022 only measured malaria), and imputing the target
    would create fake observations.
    """
    df = df.copy()
    df["year"] = df["year"].astype(int)
    df = df.drop_duplicates(subset=["year", "breakdown_dim", "subregion"])

    numeric_cols = ALL_FEATURES + [TARGET]
    for c in numeric_cols:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Drop rows with no real stunting measurement (target must be observed).
    df = df.dropna(subset=[TARGET]).reset_index(drop=True)

    # Now safe to impute FEATURES (not the target).
    for c in ALL_FEATURES:
        df[c] = df.groupby(["breakdown_dim", "year"])[c].transform(
            lambda s: s.fillna(s.median()))
        df[c] = df.groupby("year")[c].transform(
            lambda s: s.fillna(s.median()))
        df[c] = df[c].fillna(df[c].median())

    pct_cols = [c for c in numeric_cols if c.endswith("_pct") or c == TARGET]
    for c in pct_cols:
        df[c] = df[c].clip(0, 100)

    return df


def latest_year(df: pd.DataFrame) -> pd.DataFrame:
    """For the hotspot view: one row per modern region in the most recent year."""
    region_rows = df[(df["breakdown_dim"] == "Region")
                      & (df["region"].isin(CAMEROON_REGIONS))]
    if not len(region_rows):
        return df.head(0)
    most_recent = int(region_rows["year"].max())
    out = region_rows[region_rows["year"] == most_recent].copy()
    return out.drop_duplicates(subset=["region"]).reset_index(drop=True)
