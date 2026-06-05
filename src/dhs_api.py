"""Pull Cameroon DHS / MIS data from the public DHS Program API.

Unlike the HDX CSV export -- which is limited to the ``CharacteristicCategory ==
"Region"`` slice -- the API exposes every breakdown that DHS publishes
(``breakdown=all``): wealth quintile, mother's education, residence
(urban/rural), child sex, age in months, birth interval, mother's nutritional
status, etc.

We pull all of those for our 15 indicators of interest, then pivot to a wide
analysis table where each row is one *sub-population* of Cameroon:

    (year, breakdown_dim, breakdown_value)  ->  one row, ~15 indicator columns

Public API, no registration required.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
import requests

from .config import RAW_DIR

API_BASE = "https://api.dhsprogram.com/rest/dhs/data"
COUNTRY = "CM"  # Cameroon
TIMEOUT = 120

CACHE_PATH = RAW_DIR / "dhs_api_cameroon.csv"

log = logging.getLogger(__name__)


# DHS API IndicatorId -> our analysis column name + display label.
INDICATOR_MAP: dict[str, tuple[str, str]] = {
    "CN_NUTS_C_HA2": ("stunting_rate",                  "Children stunted"),
    "CN_NUTS_C_WH2": ("wasting_pct",                    "Children wasted"),
    "CN_NUTS_C_WA2": ("underweight_pct",                "Children underweight"),
    "CN_ANMC_C_ANY": ("child_anemia_pct",               "Children with any anemia"),
    "ED_LITR_W_SCH": ("women_secondary_plus_pct",       "Women with secondary or higher education"),
    "ED_LITR_W_LIT": ("women_literate_pct",             "Women who are literate"),
    "WS_SRCE_P_IMP": ("improved_water_pct",             "Population using an improved water source"),
    "WS_TLET_P_IMP": ("improved_sanitation_pct",        "Population with an improved sanitation facility"),
    "RH_ANCN_W_N4P": ("antenatal_4plus_pct",            "Antenatal visits for pregnancy: 4+ visits"),
    "RH_ANCP_W_SKP": ("antenatal_skilled_pct",          "Antenatal care from a skilled provider"),
    "RH_DELA_C_SKP": ("skilled_birth_attendance_pct",   "Assistance during delivery from a skilled provider"),
    "RH_DELP_C_DHF": ("health_facility_delivery_pct",   "Place of delivery: Health facility"),
    "AH_HINS_W_NON": ("no_health_insurance_pct",        "No health insurance [Women]"),
    "ML_PMAL_C_RDT": ("malaria_prevalence_pct",         "Malaria prevalence according to RDT"),
    "FE_FRTR_W_TFR": ("fertility_rate",                 "Total fertility rate 15-49"),
}


def _fetch_one(indicator_id: str, breakdown: str = "all") -> list[dict]:
    """Page through the DHS API for one indicator + return all data rows."""
    out: list[dict] = []
    page = 1
    while True:
        params = {
            "countryIds":   COUNTRY,
            "indicatorIds": indicator_id,
            "breakdown":    breakdown,
            "perpage":      500,
            "page":         page,
        }
        r = requests.get(API_BASE, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        j = r.json()
        data = j.get("Data", [])
        out.extend(data)
        if page >= j.get("TotalPages", 1):
            break
        page += 1
        time.sleep(0.3)   # be polite to the API
    return out


def fetch_all(use_cache: bool = True) -> pd.DataFrame:
    """Pull every indicator in INDICATOR_MAP at every breakdown for Cameroon."""
    if use_cache and CACHE_PATH.exists():
        log.info("loading cached DHS API pull: %s", CACHE_PATH)
        return pd.read_csv(CACHE_PATH)

    all_rows: list[dict] = []
    for ind_id, (col, label) in INDICATOR_MAP.items():
        log.info("fetching %s (%s)", ind_id, label)
        try:
            rows = _fetch_one(ind_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("  failed %s: %s", ind_id, exc)
            continue
        for r in rows:
            r["_feature"] = col
        all_rows.extend(rows)
        log.info("  +%d rows (running total %d)", len(rows), len(all_rows))

    if not all_rows:
        raise RuntimeError("DHS API returned no data; check network / IDs")

    raw = pd.DataFrame(all_rows)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw.to_csv(CACHE_PATH, index=False)
    log.info("cached %d raw rows -> %s", len(raw), CACHE_PATH.name)
    return raw


def to_wide(raw: pd.DataFrame) -> pd.DataFrame:
    """Pivot the long-format API dump to wide: one row per sub-population.

    Sub-population key: (SurveyYear, CharacteristicCategory, CharacteristicLabel).
    Some indicators publish multiple values per cell (e.g. by ByVariableLabel
    recall windows); we average them.
    """
    df = raw.copy()
    # Some rows have empty Value (suppressed for small samples)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.dropna(subset=["Value"])
    # Stick to indicators we know how to use
    df = df[df["_feature"].notna()]

    wide = (df.pivot_table(
                index=["SurveyYear", "CharacteristicCategory", "CharacteristicLabel"],
                columns="_feature",
                values="Value",
                aggfunc="mean",
            )
            .reset_index()
            .rename(columns={
                "SurveyYear": "year",
                "CharacteristicCategory": "breakdown_dim",
                "CharacteristicLabel":    "breakdown_value",
            }))
    wide.columns.name = None

    # health_insurance_any_pct = 100 - no_health_insurance_pct (sign flip)
    if "no_health_insurance_pct" in wide.columns:
        wide["health_insurance_any_pct"] = 100 - wide["no_health_insurance_pct"]
        wide = wide.drop(columns=["no_health_insurance_pct"])

    # Clean mojibake from breakdown_value strings
    wide["breakdown_value"] = (
        wide["breakdown_value"].astype(str)
            .str.replace("�", "", regex=False)
            .str.replace("Adamaoua/Nord/Extr�me-Nord", "Adamaoua/Nord/Extreme-Nord", regex=False)
            .str.replace("Yaound\xe9/Douala", "Yaounde/Douala", regex=False)
            .str.replace("..", "", regex=False)
            .str.strip()
    )
    wide["year"] = wide["year"].astype(int)
    return wide.sort_values(["breakdown_dim", "year", "breakdown_value"]).reset_index(drop=True)
