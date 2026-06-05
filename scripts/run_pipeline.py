"""End-to-end pipeline: data -> regression + classification + clustering + forecast.

Run this once after `pip install -r requirements.txt`. It will:
  1. Try to download HDX data; fall back to synthetic if unavailable.
  2. Clean and join into data/processed/cameroon_subregional.csv.
  3. Regression: train + evaluate every model in the zoo, write leaderboard.
  4. Classification: predict WHO risk band (low/medium/high/critical).
  5. Clustering: K-Means on socio-economic profile, profile each cluster.
  6. Forecasting: project each sub-region's stunting to 2026 + 2028.
  7. Hypothesis tests H1-H6.
  8. Write the ranked hotspot list to outputs/hotspots_ranked.csv.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src import (classification, clustering, data_loader, deployable,  # noqa: E402
                  forecasting, hypothesis_tests, modeling, preprocessing)
from src.config import OUTPUTS_DIR  # noqa: E402
from src.features import feature_matrix  # noqa: E402
from src.preprocessing import latest_year  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("pipeline")


def main() -> None:
    # ---- 1. data ----
    log.info("step 1/8: ensure data is available")
    try:
        data_loader.download_all()
    except Exception as exc:  # noqa: BLE001
        log.warning("download stage failed: %s -- continuing", exc)

    log.info("step 2/8: build analysis table")
    df = preprocessing.load_or_build()
    log.info("analysis table: %d rows x %d cols", *df.shape)

    # ---- 3. regression ----
    log.info("step 3/8: regression -- train + evaluate")
    X, y = feature_matrix(df)
    leaderboard, fitted = modeling.evaluate_all(X, y)
    leaderboard.to_csv(OUTPUTS_DIR / "model_leaderboard.csv", index=False)
    print("\n[REGRESSION leaderboard]")
    print(leaderboard.to_string(index=False))
    best_model = fitted[leaderboard.iloc[0]["name"]]
    modeling.save_best(fitted, leaderboard)

    # ---- 4. classification ----
    log.info("step 4/8: classification -- predict risk band")
    df_band = classification.add_risk_band(df)
    Xc, _ = feature_matrix(df_band)
    yc = df_band["risk_band"]
    clf_lb, clf_fit, clf_reports = classification.evaluate_all(Xc, yc)
    clf_lb.to_csv(OUTPUTS_DIR / "classifier_leaderboard.csv", index=False)
    print("\n[CLASSIFICATION leaderboard]")
    print(clf_lb.to_string(index=False))
    import json
    (OUTPUTS_DIR / "classifier_reports.json").write_text(
        json.dumps(clf_reports, indent=2), encoding="utf-8"
    )

    # ---- 5. clustering ----
    log.info("step 5/8: K-Means clustering")
    latest = latest_year(df)
    elbow = clustering.choose_k(latest)
    elbow.to_csv(OUTPUTS_DIR / "cluster_elbow.csv", index=False)
    best_k = int(elbow.sort_values("silhouette", ascending=False).iloc[0]["k"])
    log.info("best k by silhouette: %d", best_k)
    km, scaler, labels, sil = clustering.fit_kmeans(latest, k=best_k)
    latest_with_cluster = latest.copy()
    latest_with_cluster["cluster"] = labels
    profile = clustering.profile_clusters(latest, labels)
    cluster_names = clustering.label_clusters(profile)
    profile["cluster_label"] = profile["cluster"].map(cluster_names)
    latest_with_cluster["cluster_label"] = latest_with_cluster["cluster"].map(cluster_names)
    profile.to_csv(OUTPUTS_DIR / "cluster_profiles.csv", index=False)
    latest_with_cluster[["region", "subregion", "year", "cluster", "cluster_label",
                          "stunting_rate"]].to_csv(
        OUTPUTS_DIR / "cluster_assignments.csv", index=False
    )
    print(f"\n[CLUSTERING] k={best_k}, silhouette={sil:.3f}")
    print(profile.to_string(index=False))

    # ---- 6. forecasting ----
    log.info("step 6/8: per-sub-region forecasts")
    trends = forecasting.fit_trends(df)
    fc = forecasting.forecast(df)
    trends.to_csv(OUTPUTS_DIR / "trends.csv", index=False)
    fc.to_csv(OUTPUTS_DIR / "forecasts.csv", index=False)
    print("\n[FORECAST] mean stunting by future year:")
    print(fc.groupby("year")["forecast_stunting"].mean().round(2).to_string())

    # ---- 7. hypothesis tests ----
    log.info("step 7/8: hypothesis tests H1-H6")
    h = hypothesis_tests.run_all(df, model=best_model, X=X, y=y)
    h.to_csv(OUTPUTS_DIR / "hypothesis_tests.csv", index=False)
    print("\n[HYPOTHESIS TESTS]")
    print(h.to_string(index=False))

    # ---- 8. ranked hotspots ----
    log.info("step 8/8: ranked hotspots")
    X_latest, _ = feature_matrix(latest)
    meta = latest[["region", "subregion", "year"]]
    ranked = modeling.predict_hotspots(best_model, X_latest, meta)
    # Add risk band predictions from the best classifier.
    best_clf = clf_fit[clf_lb.iloc[0]["name"]]
    bands = classification.predict_risk_bands(best_clf, X_latest, meta)
    ranked = ranked.merge(bands[["region", "subregion", "predicted_band"]],
                           on=["region", "subregion"], how="left")
    # Add the cluster + forecast.
    ranked = ranked.merge(
        latest_with_cluster[["region", "subregion", "cluster", "cluster_label"]],
        on=["region", "subregion"], how="left"
    )
    fc_pivot = (fc.pivot_table(index=["region", "subregion"], columns="year",
                                values="forecast_stunting")
                  .add_prefix("forecast_").reset_index())
    ranked = ranked.merge(fc_pivot, on=["region", "subregion"], how="left")
    ranked.to_csv(OUTPUTS_DIR / "hotspots_ranked.csv", index=False)
    print("\n[TOP 10 HOTSPOTS]")
    print(ranked.head(10).to_string(index=False))

    # ---- bonus: deployable models for the website's predictor ----
    log.info("exporting deployable models for client-side inference")
    path = deployable.write_payload(df)
    log.info("predictor payload -> %s", path)


if __name__ == "__main__":
    main()
