"""Stitch real DHS / MICS Cameroon CSVs into the analysis-ready wide table.

Each downloaded CSV is in DHS long format:
    ISO3, CountryName, SurveyYear, SurveyType, Indicator, CharacteristicLabel,
    CharacteristicCategory, Value, ...

We:
  1. Normalise region names (handle 1991/1998 mega-regions, encoding mojibake,
     city/region splits in 2004+).
  2. Filter each CSV to the indicators we want and pivot to wide.
  3. Outer-merge across all sources on (region, year).

The resulting frame has exactly one row per (Cameroonian admin-1 region, real
DHS/MICS survey year) with as many real columns as we can recover.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .config import RAW_DIR, SURVEY_YEARS

log = logging.getLogger(__name__)
DHS_DIR = RAW_DIR / "dhs_subnational"


# -------- region name normalisation ---------------------------------------

# Canonical Cameroon admin-1 region names (matching our config + GeoJSON).
CANONICAL_REGIONS = [
    "Adamawa", "Centre", "East", "Far North", "Littoral",
    "North", "Northwest", "South", "Southwest", "West",
]

# Map *individual* DHS region labels (with prefix/encoding variants) to canonical.
# The leading ".." appears in DHS CSVs to indicate "indented" sub-region rows.
_INDIVIDUAL_REGIONS: dict[str, str] = {
    # Adamawa
    "Adamaoua": "Adamawa", "Adamawa": "Adamawa",
    # Centre (regions, plus Yaoundé that DHS splits out as its own city row)
    "Centre": "Centre", "Centro": "Centre", "Yaound\xe9": "Centre",
    "Yaounde": "Centre",
    # East
    "Est": "East", "East": "East",
    # Far North (UTF / mojibake variants)
    "Extr\xeame-Nord": "Far North", "Extreme-Nord": "Far North",
    "Far North": "Far North", "Far-North": "Far North",
    # Littoral (plus Douala that DHS splits as its own city row)
    "Littoral": "Littoral", "Douala": "Littoral",
    # North
    "Nord": "North", "North": "North",
    # Northwest
    "Nord Ouest": "Northwest", "Nord-Ouest": "Northwest",
    "North West": "Northwest", "North-West": "Northwest", "Northwest": "Northwest",
    # South
    "Sud": "South", "South": "South",
    # Southwest
    "Sud Ouest": "Southwest", "Sud-Ouest": "Southwest",
    "South West": "Southwest", "South-West": "Southwest", "Southwest": "Southwest",
    # West
    "Ouest": "West", "West": "West",
}

# 1991 / 1998 "mega-regions" -- broadcast each mega's value to its constituent regions.
_MEGA_REGIONS: dict[str, list[str]] = {
    "Adamaoua/Nord/Extreme-Nord":  ["Adamawa", "North", "Far North"],
    "Centre/Sud/Est":              ["Centre", "South", "East"],
    "Nord Ouest/Sud Ouest":        ["Northwest", "Southwest"],
    "Ouest/Littoral":              ["West", "Littoral"],
    "Yaounde/Douala":              ["Centre", "Littoral"],
}


def _clean_label(raw: str) -> str:
    """Strip DHS ".." prefix, normalise encoding mojibake to plain ASCII."""
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return ""
    s = str(raw).strip().lstrip(".").strip()
    # The HDX export double-encodes UTF-8 into latin-1 sometimes; replace the
    # common Cameroon-specific mojibake we see in the CSVs.
    s = (s.replace("�", "")          # raw replacement char
           .replace("Extr\xeame-Nord", "Extreme-Nord")
           .replace("Yaound\xe9", "Yaounde")
           .replace("Extrme-Nord", "Extreme-Nord")
           .replace("Extrême-Nord", "Extreme-Nord")
           .replace("Yaound", "Yaounde").replace("Yaoundee", "Yaounde"))
    return s


def expand_region_label(raw: str) -> list[str]:
    """Resolve a raw DHS region label to one or more canonical region names.

    Returns a list because old-survey mega-regions broadcast to several regions.
    """
    s = _clean_label(raw)
    if not s:
        return []
    if s in _INDIVIDUAL_REGIONS:
        return [_INDIVIDUAL_REGIONS[s]]
    if s in _MEGA_REGIONS:
        return _MEGA_REGIONS[s]
    # try mojibake-tolerant lookup
    for k, canon in _INDIVIDUAL_REGIONS.items():
        if k.lower() == s.lower():
            return [canon]
    for k, members in _MEGA_REGIONS.items():
        if k.lower() == s.lower():
            return members
    return []


# -------- indicator -> feature map ----------------------------------------
# Each entry: (preferred CSV stem, exact Indicator string, sign, post-fn)
# `sign` is +1 if the indicator is the feature directly, -1 if the feature is
# "100 - indicator" (e.g. no-education %), and post-fn lets us scale (e.g. /100).

FEATURE_MAP: dict[str, dict] = {
    # Target
    "stunting_rate": {"csv": "Anthropometry_Data_for_Cameroon.csv",
                       "indicator": "Children stunted"},

    # Nutrition siblings (also useful as predictors of stunting trajectory)
    "wasting_pct":       {"csv": "Anthropometry_Data_for_Cameroon.csv",
                           "indicator": "Children wasted"},
    "underweight_pct":   {"csv": "Anthropometry_Data_for_Cameroon.csv",
                           "indicator": "Children underweight"},
    "child_anemia_pct":  {"csv": "Anemia_Data_for_Cameroon.csv",
                           "indicator": "Children with any anemia"},

    # Maternal education
    "women_secondary_plus_pct": {"csv": "Literacy_Data_for_Cameroon.csv",
                                  "indicator": "Women with secondary or higher education"},
    "women_literate_pct":       {"csv": "Literacy_Data_for_Cameroon.csv",
                                  "indicator": "Women who are literate"},

    # WASH
    "improved_water_pct":      {"csv": "Water_Data_for_Cameroon.csv",
                                "indicator": "Population using an improved water source"},
    "improved_sanitation_pct": {"csv": "Toilet_Facilities_Data_for_Cameroon.csv",
                                "indicator": "Population with an improved sanitation facility"},

    # Maternal / healthcare access
    "antenatal_4plus_pct":          {"csv": "MDGs_Data_for_Cameroon.csv",
                                      "indicator": "Antenatal visits for pregnancy: 4+ visits"},
    "skilled_birth_attendance_pct": {"csv": "Access_to_Health_Care_Data_for_Cameroon.csv",
                                      "indicator": "Assistance during delivery from a skilled provider"},
    "health_facility_delivery_pct": {"csv": "Access_to_Health_Care_Data_for_Cameroon.csv",
                                      "indicator": "Place of delivery: Health facility"},
    "antenatal_skilled_pct":        {"csv": "Access_to_Health_Care_Data_for_Cameroon.csv",
                                      "indicator": "Antenatal care from a skilled provider"},

    # Insurance
    "health_insurance_any_pct": {"csv": "Health_Insurance_Data_for_Cameroon.csv",
                                  "indicator": "No health insurance [Women]",
                                  "transform": lambda v: 100 - v},

    # Disease burden
    "malaria_prevalence_pct": {"csv": "Malaria_Parasitemia_Data_for_Cameroon.csv",
                                "indicator": "Malaria prevalence according to RDT"},

    # Demographics
    "fertility_rate": {"csv": "DHS_Mobile_Data_for_Cameroon.csv",
                        "indicator": "Total fertility rate 15-49"},
}


# -------- loader -----------------------------------------------------------

def _load_long(csv: Path, indicator: str) -> pd.DataFrame:
    """Load one CSV and return long-format (region, year, value) tuples."""
    df = pd.read_csv(csv, encoding="utf-8", encoding_errors="replace",
                      usecols=["Indicator", "CharacteristicLabel",
                                "CharacteristicCategory", "SurveyYear",
                                "Value", "ByVariableLabel", "IsTotal"])
    df = df[df["Indicator"] == indicator]
    df = df[df["CharacteristicCategory"] == "Region"]

    # Some indicators (e.g. delivery / antenatal) are *only* published with a
    # recall window in ByVariableLabel ("Five years preceding the survey").
    # Strategy:
    #   - If a row has no ByVariableLabel, prefer it (single canonical value).
    #   - Otherwise, prefer the longest recall window when "five years" is
    #     available (more rows = more stable), else "three years", else "two".
    if "ByVariableLabel" in df.columns and len(df):
        empty_mask = df["ByVariableLabel"].isna() | (df["ByVariableLabel"] == "")
        if empty_mask.any():
            df = df[empty_mask]
        else:
            for pref in ("five years preceding", "three years preceding",
                          "two years preceding"):
                want = df["ByVariableLabel"].str.lower().str.contains(pref, na=False)
                if want.any():
                    df = df[want]
                    break
    return df[["CharacteristicLabel", "SurveyYear", "Value"]]


def _explode_regions(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Expand each DHS row into one row per canonical Cameroon region."""
    out = []
    for _, row in raw_df.iterrows():
        regions = expand_region_label(row["CharacteristicLabel"])
        if not regions:
            continue
        for r in regions:
            out.append({"region": r,
                         "year": int(row["SurveyYear"]),
                         "value": float(row["Value"])})
    if not out:
        return pd.DataFrame(columns=["region", "year", "value"])
    # Where mega-regions broadcast OR multiple raw rows resolve to the same
    # (region, year), take the mean.
    return (pd.DataFrame(out)
              .groupby(["region", "year"], as_index=False)["value"].mean())


def load_real_subnational(years: list[int] | None = None) -> pd.DataFrame:
    """Build the wide analysis table from real DHS/MICS CSVs."""
    years = years or SURVEY_YEARS

    if not DHS_DIR.exists():
        raise FileNotFoundError(f"raw DHS folder missing: {DHS_DIR}")

    # Start with the full (region, year) grid -- 10 x len(years) rows -- then
    # left-join each feature into it.
    grid = pd.MultiIndex.from_product(
        [CANONICAL_REGIONS, years], names=["region", "year"]
    ).to_frame(index=False)

    out = grid
    for feature, spec in FEATURE_MAP.items():
        csv = DHS_DIR / spec["csv"]
        if not csv.exists():
            log.warning("skip %s: source CSV missing (%s)", feature, csv.name)
            continue
        try:
            long = _load_long(csv, spec["indicator"])
        except Exception as exc:  # noqa: BLE001
            log.warning("skip %s: load failed (%s)", feature, exc)
            continue
        if long.empty:
            log.warning("skip %s: no rows matched indicator", feature)
            continue
        wide = _explode_regions(long).rename(columns={"value": feature})
        if "transform" in spec:
            wide[feature] = wide[feature].apply(spec["transform"])
        out = out.merge(wide, on=["region", "year"], how="left")
        log.info("merged %-30s n_non_null=%3d", feature, out[feature].notna().sum())

    out = out.sort_values(["year", "region"]).reset_index(drop=True)
    log.info("final real table: %d rows x %d cols", *out.shape)
    return out
