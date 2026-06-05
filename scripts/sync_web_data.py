"""Sync the Python pipeline outputs into the Next.js site's public folder.

After `python scripts/run_pipeline.py` produces:
    outputs/model_leaderboard.csv
    outputs/hypothesis_tests.csv
    outputs/hotspots_ranked.csv
    data/processed/cameroon_subregional.csv

this script converts them to JSON and drops them in web/public/data/, where
they're statically importable from the Next.js app at build time.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

WEB_DATA = ROOT / "web" / "public" / "data"


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """JSON-safe records (NaN -> None, numpy ints/floats -> Python)."""
    return json.loads(df.to_json(orient="records"))


def build_summary(sub: pd.DataFrame, hotspots: pd.DataFrame,
                  leaderboard: pd.DataFrame, hypotheses: pd.DataFrame) -> dict:
    latest_year = int(sub["year"].max())
    latest = sub[sub["year"] == latest_year]
    best = leaderboard.iloc[0]
    h6 = hypotheses[hypotheses["hypothesis"] == "H6"].iloc[0] \
        if (hypotheses["hypothesis"] == "H6").any() else None

    return {
        "n_regions": int(sub["region"].nunique()),
        "n_subregions": int(sub["subregion"].nunique()),
        "survey_years": sorted(sub["year"].unique().tolist()),
        "latest_year": latest_year,
        "national_mean_stunting": round(float(latest["stunting_rate"].mean()), 1),
        "worst_subregion_pct": round(float(latest["stunting_rate"].max()), 1),
        "best_subregion_pct": round(float(latest["stunting_rate"].min()), 1),
        "best_model": str(best["name"]),
        "best_cv_rmse": round(float(best["cv_rmse_mean"]), 3),
        "baseline_cv_rmse": round(
            float(leaderboard.loc[leaderboard["name"] == "Baseline (mean)",
                                   "cv_rmse_mean"].iloc[0]), 3
        ),
        "improvement_pct": round(float(h6["improvement_pct"]), 1) if h6 is not None else None,
        "n_hypotheses_supported": int(hypotheses["reject_null"].sum()),
        "n_hypotheses_total": int(len(hypotheses)),
    }


def main() -> None:
    WEB_DATA.mkdir(parents=True, exist_ok=True)

    sub = pd.read_csv(ROOT / "data" / "processed" / "cameroon_subregional.csv")
    hotspots = pd.read_csv(ROOT / "outputs" / "hotspots_ranked.csv")
    leaderboard = pd.read_csv(ROOT / "outputs" / "model_leaderboard.csv")
    hypotheses = pd.read_csv(ROOT / "outputs" / "hypothesis_tests.csv")

    # New analyses (graceful skip if missing)
    def _load(p):
        path = ROOT / "outputs" / p
        return pd.read_csv(path) if path.exists() else pd.DataFrame()

    clf_lb           = _load("classifier_leaderboard.csv")
    cluster_profiles = _load("cluster_profiles.csv")
    cluster_assigns  = _load("cluster_assignments.csv")
    elbow            = _load("cluster_elbow.csv")
    trends           = _load("trends.csv")
    forecasts        = _load("forecasts.csv")

    classifier_reports = {}
    rep_path = ROOT / "outputs" / "classifier_reports.json"
    if rep_path.exists():
        classifier_reports = json.loads(rep_path.read_text(encoding="utf-8"))

    predictor_payload = {}
    pred_path = ROOT / "outputs" / "predictor.json"
    if pred_path.exists():
        predictor_payload = json.loads(pred_path.read_text(encoding="utf-8"))

    # Round numerics so the JSON stays small + readable.
    for df in (hotspots, leaderboard, clf_lb, cluster_profiles,
                trends, forecasts):
        for c in df.select_dtypes("float").columns:
            df[c] = df[c].round(3)

    # Regional aggregates for the choropleth map.
    region_agg = (hotspots.groupby("region", as_index=False)["predicted_stunting"]
                          .agg(["mean", "max", "count"])
                          .rename(columns={"mean": "predicted_stunting_mean",
                                            "max":  "predicted_stunting_max",
                                            "count": "n_subregions"})
                          .round(2)
                          .reset_index())

    payloads = {
        "summary.json":            build_summary(sub, hotspots, leaderboard, hypotheses),
        "subregional.json":        df_to_records(sub),
        "hotspots.json":           df_to_records(hotspots),
        "leaderboard.json":        df_to_records(leaderboard),
        "hypotheses.json":         df_to_records(hypotheses),
        "regions.json":            df_to_records(region_agg),
        "classifier_leaderboard.json": df_to_records(clf_lb),
        "classifier_reports.json": classifier_reports,
        "cluster_profiles.json":   df_to_records(cluster_profiles),
        "cluster_assignments.json": df_to_records(cluster_assigns),
        "cluster_elbow.json":      df_to_records(elbow),
        "trends.json":             df_to_records(trends),
        "forecasts.json":          df_to_records(forecasts),
        "predictor.json":          predictor_payload,
    }

    for name, payload in payloads.items():
        path = WEB_DATA / name
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        size_kb = path.stat().st_size / 1024
        print(f"  wrote {name:22s}  {size_kb:7.1f} KB")

    print(f"\nAll data synced to {WEB_DATA}")


if __name__ == "__main__":
    main()
