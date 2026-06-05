"""Generate a realistic synthetic Cameroon sub-regional dataset.

This is the fallback used when HDX downloads fail or when we want
fully reproducible pipeline runs. The schema and variable ranges
mirror DHS / WHO / HDX sources for Cameroon and are calibrated to
real published national means (e.g. ~29% under-5 stunting nationally,
strong North > South gradient).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import CAMEROON_REGIONS, DHS_SURVEY_YEARS


# Sub-regions (departments) per region. Cameroon has 58 departments
# spread across 10 regions; counts here match official admin divisions.
SUBREGIONS_PER_REGION: dict[str, list[str]] = {
    "Adamawa":   ["Djerem", "Faro-et-Deo", "Mayo-Banyo", "Mbere", "Vina"],
    "Centre":    ["Haute-Sanaga", "Lekie", "Mbam-et-Inoubou", "Mbam-et-Kim",
                  "Mefou-et-Afamba", "Mefou-et-Akono", "Mfoundi", "Nyong-et-Kelle",
                  "Nyong-et-Mfoumou", "Nyong-et-Soo"],
    "East":      ["Boumba-et-Ngoko", "Haut-Nyong", "Kadey", "Lom-et-Djerem"],
    "Far North": ["Diamare", "Logone-et-Chari", "Mayo-Danay", "Mayo-Kani",
                  "Mayo-Sava", "Mayo-Tsanaga"],
    "Littoral":  ["Moungo", "Nkam", "Sanaga-Maritime", "Wouri"],
    "North":     ["Benoue", "Faro", "Mayo-Louti", "Mayo-Rey"],
    "Northwest": ["Boyo", "Bui", "Donga-Mantung", "Menchum", "Mezam",
                  "Momo", "Ngoketunjia"],
    "South":     ["Dja-et-Lobo", "Mvila", "Ocean", "Vallee-du-Ntem"],
    "Southwest": ["Fako", "Koupe-Manengouba", "Lebialem", "Manyu", "Meme", "Ndian"],
    "West":      ["Bamboutos", "Hauts-Plateaux", "Haut-Nkam", "Koung-Khi",
                  "Menoua", "Mifi", "Nde", "Noun"],
}

# Region-level base profile. Numbers reflect the well-documented north / south
# gradient: the three northern regions (Far North, North, Adamawa) are poorer,
# drier, with less schooling and higher stunting; Centre and Littoral host
# Yaounde and Douala respectively and are wealthier and more urban.
# Profile "stunting" values are intercepts -- the final synthetic stunting also
# absorbs each region's feature deviations from the national mean, which shifts
# the per-region mean. We pre-compensate the intercepts so the 2018 mean of
# each region lands near published DHS values.
_REGION_PROFILE: dict[str, dict[str, float]] = {
    "Far North": dict(stunting=29, edu=2.5, water=48, sanit=21, wealth=-1.1,
                       malaria=38, urban=18, density=130, fac=0.6),
    "North":     dict(stunting=28, edu=3.0, water=52, sanit=24, wealth=-0.9,
                       malaria=35, urban=22, density=70,  fac=0.7),
    "Adamawa":   dict(stunting=26, edu=3.5, water=55, sanit=28, wealth=-0.7,
                       malaria=30, urban=25, density=20,  fac=0.8),
    "East":      dict(stunting=28, edu=4.5, water=50, sanit=32, wealth=-0.6,
                       malaria=33, urban=30, density=12,  fac=0.9),
    "Northwest": dict(stunting=25, edu=5.5, water=63, sanit=42, wealth=-0.2,
                       malaria=22, urban=42, density=110, fac=1.2),
    "Southwest": dict(stunting=26, edu=6.5, water=70, sanit=48, wealth=0.1,
                       malaria=24, urban=46, density=85,  fac=1.3),
    "West":      dict(stunting=27, edu=6.8, water=72, sanit=52, wealth=0.2,
                       malaria=18, urban=48, density=170, fac=1.4),
    "South":     dict(stunting=27, edu=7.0, water=68, sanit=50, wealth=0.3,
                       malaria=26, urban=44, density=18,  fac=1.1),
    "Centre":    dict(stunting=30, edu=8.5, water=82, sanit=68, wealth=0.7,
                       malaria=16, urban=70, density=200, fac=1.8),
    "Littoral":  dict(stunting=22, edu=8.8, water=86, sanit=72, wealth=0.9,
                       malaria=15, urban=82, density=320, fac=2.0),
}


def _temporal_factor(year: int) -> float:
    """Years before / after 2018 (the DHS reference year).

    Cameroon's real annual progress is small (~0.5pp/year on stunting), so all
    temporal coefficients in the stunting formula are scaled accordingly. The
    factor is plain ``(2018 - year)`` so a one-unit change is one calendar
    year, which keeps the per-year deltas easy to reason about.
    """
    return float(2018 - year)


def build_dataset(seed: int = 42, years: list[int] | None = None) -> pd.DataFrame:
    """Build the long-format sub-regional dataset across survey years."""
    rng = np.random.default_rng(seed)
    years = years or DHS_SURVEY_YEARS

    rows = []
    for region, subregions in SUBREGIONS_PER_REGION.items():
        prof = _REGION_PROFILE[region]
        for sub in subregions:
            # Per-sub-region deviation from the regional baseline (kept stable
            # across years so the same place looks like itself over time).
            dev = rng.normal(0, 1.0)

            for year in years:
                # ``t`` is now (2018 - year) in absolute years -- temporal
                # coefficients below are calibrated as per-year deltas.
                t = _temporal_factor(year)

                # Annual deltas (per-year improvement): education +0.15 yrs,
                # water +1.0pp, sanitation +1.2pp, wealth +0.04, malaria -0.5pp,
                # urban +0.7pp, facility density +0.04 per 10k, fertility -0.05.
                edu     = max(0, prof["edu"]    - 0.15 * t + 0.4 * dev + rng.normal(0, 0.4))
                water   = np.clip(prof["water"]   - 1.0 * t + 3 * dev + rng.normal(0, 4),  5, 99)
                sanit   = np.clip(prof["sanit"]   - 1.2 * t + 3 * dev + rng.normal(0, 4),  5, 95)
                wealth  = prof["wealth"]  + 0.3 * dev - 0.04 * t + rng.normal(0, 0.15)
                malaria = np.clip(prof["malaria"] + 0.5 * t - 1.5 * dev + rng.normal(0, 2.5), 2, 70)
                urban   = np.clip(prof["urban"]   - 0.7 * t + 4 * dev + rng.normal(0, 3),   5, 98)
                density = max(2.0, prof["density"] * (1 - 0.025 * t) * (1 + 0.15 * dev)
                              + rng.normal(0, 6))
                fac     = max(0.1, prof["fac"]    - 0.04 * t + 0.2 * dev + rng.normal(0, 0.15))
                anc4    = np.clip(35 + 4 * edu + 8 * wealth - 1.0 * t + rng.normal(0, 5), 5, 98)
                sba     = np.clip(30 + 5 * edu + 10 * wealth - 1.5 * t + rng.normal(0, 6), 5, 99)
                ins     = np.clip(1 + 1.5 * (wealth + 1) - 0.4 * t + rng.normal(0, 1), 0.1, 30)
                anemia  = np.clip(55 - 1.5 * edu - 3 * wealth + 0.2 * malaria + rng.normal(0, 4), 15, 85)
                poverty = np.clip(55 - 12 * (wealth + 1) - 4 * edu + 1.0 * t + rng.normal(0, 5), 2, 95)
                fert    = np.clip(7.0 - 0.25 * edu - 0.4 * (wealth + 1) + 0.04 * t + rng.normal(0, 0.3), 1.5, 8)

                # Target: stunting rate. We centre each driver on a plausible
                # national-mean value so the coefficients act on *deviations*
                # rather than absolute levels -- this keeps each region's mean
                # tracking ``prof["stunting"]`` instead of being dragged down
                # by features that happen to be large in absolute terms.
                stunting = (
                    prof["stunting"] + 0.35 * t
                    - 0.9  * (edu     - 6.0)
                    - 0.05 * (water  - 65)
                    - 0.04 * (sanit  - 45)
                    - 2.0  * (wealth  - 0.0)
                    - 0.6  * (fac     - 1.1)
                    + 0.09 * (malaria - 25)
                    + 0.03 * (anemia  - 45)
                    + 0.05 * (poverty - 35)
                    + 0.4 * dev
                    + rng.normal(0, 2.0)
                )
                stunting = float(np.clip(stunting, 3, 65))

                rows.append({
                    "region": region,
                    "subregion": sub,
                    "year": year,
                    # features
                    "maternal_education_years":      round(edu, 2),
                    "antenatal_visits_4plus_pct":    round(anc4, 1),
                    "improved_water_pct":            round(water, 1),
                    "improved_sanitation_pct":       round(sanit, 1),
                    "wealth_index":                  round(wealth, 3),
                    "poverty_headcount_pct":         round(poverty, 1),
                    "facilities_per_10k":            round(fac, 2),
                    "skilled_birth_attendance_pct":  round(sba, 1),
                    "health_insurance_coverage_pct": round(ins, 2),
                    "malaria_prevalence_pct":        round(malaria, 1),
                    "anemia_under5_pct":             round(anemia, 1),
                    "population_density":            round(density, 1),
                    "urban_share_pct":               round(urban, 1),
                    "fertility_rate":                round(fert, 2),
                    # target
                    "stunting_rate":                 round(stunting, 1),
                })

    df = pd.DataFrame(rows)
    return df.sort_values(["year", "region", "subregion"]).reset_index(drop=True)


def write_synthetic(path) -> None:
    df = build_dataset()
    df.to_csv(path, index=False)
