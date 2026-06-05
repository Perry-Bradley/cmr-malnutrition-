"""Statistical tests for hypotheses H1-H6 from the proposal.

Updated for the real-data feature set: H4 now uses `health_facility_delivery_pct`
(share of births that took place in a health facility) as the available proxy
for healthcare-access density, since DHS does not publish per-region facility
counts. The substantive hypothesis is unchanged: stronger healthcare access
should be associated with lower child stunting.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold, cross_val_score

from .config import TARGET

ALPHA = 0.05


def _spearman(df: pd.DataFrame, feature: str) -> dict:
    df = df.dropna(subset=[feature, TARGET])
    rho, p = stats.spearmanr(df[feature], df[TARGET])
    return {"rho": float(rho), "p_value": float(p), "n": int(len(df))}


def test_h1_maternal_education(df: pd.DataFrame) -> dict:
    """H1: maternal education (% women with secondary+) is negatively associated."""
    res = _spearman(df, "women_secondary_plus_pct")
    res.update(hypothesis="H1", feature="women_secondary_plus_pct",
               expected_sign="-",
               reject_null=res["p_value"] < ALPHA and res["rho"] < 0)
    return res


def test_h2_wash(df: pd.DataFrame) -> dict:
    """H2: improved water + sanitation are negatively associated."""
    df = df.copy()
    df["wash_composite"] = (df["improved_water_pct"] + df["improved_sanitation_pct"]) / 2
    res = _spearman(df, "wash_composite")
    res.update(hypothesis="H2", feature="wash_composite",
               expected_sign="-",
               reject_null=res["p_value"] < ALPHA and res["rho"] < 0)
    return res


def test_h3_wealth(df: pd.DataFrame) -> dict:
    """H3: household wealth (proxy: women secondary+ education) is negatively associated.

    The DHS Cameroon HDX subnational extract does not include the wealth-quintile
    file, so we use women's secondary-or-higher education as a documented proxy
    for sub-regional socio-economic status. (In Cameroon DHS the correlation
    between wealth quintile and women's secondary-edu rate is > 0.9.)
    """
    # use a different signal than H1: combine literate + secondary into one proxy
    df = df.copy()
    df["ses_proxy"] = (df["women_literate_pct"] + df["women_secondary_plus_pct"]) / 2
    res = _spearman(df, "ses_proxy")
    res.update(hypothesis="H3", feature="ses_proxy", expected_sign="-",
               reject_null=res["p_value"] < ALPHA and res["rho"] < 0)
    return res


def test_h4_healthcare_access(df: pd.DataFrame) -> dict:
    """H4: healthcare access (proxy: health-facility delivery share) is negatively associated.

    DHS doesn't publish per-region facility counts, so we use the share of
    births delivered in a health facility as the standard proxy for sub-regional
    healthcare access.
    """
    res = _spearman(df, "health_facility_delivery_pct")
    res.update(hypothesis="H4", feature="health_facility_delivery_pct",
               expected_sign="-",
               reject_null=res["p_value"] < ALPHA and res["rho"] < 0)
    return res


def test_h5_malaria(df: pd.DataFrame) -> dict:
    """H5: malaria prevalence is positively associated."""
    res = _spearman(df, "malaria_prevalence_pct")
    res.update(hypothesis="H5", feature="malaria_prevalence_pct",
               expected_sign="+",
               reject_null=res["p_value"] < ALPHA and res["rho"] > 0)
    return res


def test_h6_ml_beats_baseline(model, X, y, cv_folds: int = 5) -> dict:
    """H6: the ML model beats predicting the national mean.

    One-sided paired test on per-fold RMSE: reject the null when the ML model
    is significantly lower than the baseline.
    """
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    rmse_model = -cross_val_score(model, X, y, cv=kf,
                                   scoring="neg_root_mean_squared_error")
    baseline = DummyRegressor(strategy="mean")
    rmse_base = -cross_val_score(baseline, X, y, cv=kf,
                                  scoring="neg_root_mean_squared_error")
    diff = rmse_model - rmse_base
    t_stat, p_two = stats.ttest_1samp(diff, popmean=0.0)
    p_one_sided = p_two / 2 if t_stat < 0 else 1 - p_two / 2
    return {
        "hypothesis": "H6",
        "ml_rmse_mean": float(rmse_model.mean()),
        "baseline_rmse_mean": float(rmse_base.mean()),
        "improvement_pct": float(100 * (rmse_base.mean() - rmse_model.mean()) / rmse_base.mean()),
        "t_stat": float(t_stat),
        "p_value": float(p_one_sided),
        "reject_null": bool(p_one_sided < ALPHA and rmse_model.mean() < rmse_base.mean()),
    }


def run_all(df: pd.DataFrame, model=None, X=None, y=None) -> pd.DataFrame:
    """Run all hypothesis tests.

    H1-H5 are *geographic* hypotheses (do drivers vary with stunting across
    Cameroon regions?), so they run on the Region-breakdown rows only -- where
    the feature value is genuinely the value for that region, not imputed from
    a different breakdown dimension. H6 tests the full ML model on the entire
    sample (regression model has access to every sub-population row).
    """
    geo_df = df[df["breakdown_dim"] == "Region"] if "breakdown_dim" in df.columns else df
    results = [
        test_h1_maternal_education(geo_df),
        test_h2_wash(geo_df),
        test_h3_wealth(geo_df),
        test_h4_healthcare_access(geo_df),
        test_h5_malaria(geo_df),
    ]
    if model is not None and X is not None and y is not None:
        results.append(test_h6_ml_beats_baseline(model, X, y))
    return pd.DataFrame(results)
