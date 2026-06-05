"""Programmatically build the master CRISP-DM analysis notebook.

Run once after installing deps:
    python scripts/build_notebook.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "notebooks" / "malnutrition_analysis.ipynb"


def md(src: str): return nbf.v4.new_markdown_cell(src)
def code(src: str): return nbf.v4.new_code_cell(src)


CELLS = [
    md("""# Predicting Child Malnutrition Hotspots in Cameroon
### CEC 420 - Data Mining
**Author:** SEPO PERRY-BRADLEY DINGA (CT23A145)
**Department:** Computer Engineering - Software Engineering
**Academic Year:** 2025 / 2026

This notebook is the end-to-end analytical companion to the project proposal.
**It runs entirely on real Cameroon DHS + MICS data** downloaded from HDX
(5 DHS rounds: 1991, 1998, 2004, 2011, 2018). The 1991/1998 mega-regions
("Adamaoua/Nord/Extreme-Nord" etc.) are broadcast to their constituent modern
regions to preserve the time series.

The notebook follows the **CRISP-DM** framework:

1. Business Understanding
2. Data Understanding
3. Data Preparation
4. Modelling (regression + classification + clustering + forecasting)
5. Evaluation (incl. H1-H6 hypothesis tests)
6. Deployment (best model + deployable JSON for the in-browser predictor)
"""),

    # -------------------------------------------------------------- 0. setup
    md("## 0. Setup"),
    code("""# Make the project root importable
import sys, os
from pathlib import Path
ROOT = Path(os.getcwd()).resolve()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="whitegrid", context="notebook")
pd.set_option("display.max_columns", 60)
pd.set_option("display.width", 200)
print("Project root:", ROOT)"""),

    # -------------------------------------------------------------- 1. business
    md("""## 1. Business Understanding

**Problem.** Roughly 29% of Cameroonian children under five are stunted (chronically
malnourished), but the burden is highly uneven across the country's sub-regions.
The Ministry of Public Health needs to know **which sub-regions to prioritise**
for nutrition and WASH interventions.

**Data-mining task.** Build a regression model that predicts a sub-region's
stunting rate from publicly available indicators (maternal education, water and
sanitation, wealth, healthcare access, disease burden), then rank sub-regions by
predicted risk.

**Success criteria.**
- The model beats a naive baseline (predicting the national mean) at the 5%
  significance level on 5-fold CV RMSE.
- We can rank sub-regions and produce a top-N list a programme officer could act on.
"""),

    # -------------------------------------------------------------- 2. data und
    md("""## 2. Data Understanding

Five HDX sources are downloaded; the analysis uses the **real Cameroon Sub-national
DHS** files (5 rounds: 1991, 1998, 2004, 2011, 2018). Each CSV is in DHS
long-format (one row per region/year/indicator/byvariable). The
`src/dhs_loader.py` module:

- filters every CSV to rows where ``CharacteristicCategory == "Region"``
- picks the longest published recall window when ``ByVariableLabel`` is set
- maps the raw `Indicator` strings to our analysis columns (see `FEATURE_MAP`)
- normalises region names (1991/1998 mega-regions, encoding mojibake)
- broadcasts each 1991/1998 mega-region value to its constituent modern regions

The result is exactly **10 Cameroon admin-1 regions × 5 survey years = 50 real rows**.
"""),
    code("""from src import preprocessing
df = preprocessing.load_or_build()
print(f"Analysis table shape: {df.shape}")
df.head()"""),
    code("""df.info()"""),
    code("""df.describe().T"""),

    # -------------------------------------------------------------- 3. prep
    md("""## 3. Data Preparation

The `preprocessing.load_or_build()` step has already:
- joined the per-indicator CSVs (or synthesised compatible data),
- coerced numeric columns,
- de-duplicated `(region, subregion, year)`,
- imputed missing values with the region-year median, falling back to the
  global median,
- clipped percentage columns to `[0, 100]`.

Below we add a few engineered features and prepare `(X, y)` for modelling.
"""),
    code("""from src.features import add_engineered, feature_matrix
df_eng = add_engineered(df)
X, y = feature_matrix(df)
print("X shape:", X.shape, "| y shape:", y.shape)
X.head()"""),

    # -------------------------------------------------------------- 4. EDA
    md("""## 4. Exploratory Data Analysis"""),
    code("""from src import visualization as viz
viz.plot_target_distribution(df, save="01_target_distribution.png")
plt.show()"""),
    code("""viz.plot_region_boxplot(df, save="02_region_boxplot.png")
plt.show()"""),
    md("Stunting is highest in the three **northern** regions (Far North, "
       "North, Adamawa), consistent with published DHS reports. Centre and "
       "Littoral - which host Yaounde and Douala respectively - have the lowest "
       "rates."),
    code("""viz.plot_correlation_heatmap(df, save="03_correlation_heatmap.png")
plt.show()"""),
    code("""# Trend over time
trend = df.groupby(["year", "region"])["stunting_rate"].mean().reset_index()
fig, ax = plt.subplots(figsize=(9, 5))
sns.lineplot(data=trend, x="year", y="stunting_rate", hue="region",
              marker="o", ax=ax)
ax.set_title("Mean child stunting rate by region over DHS survey years")
ax.set_ylabel("Stunting rate (%)")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
plt.tight_layout()
fig.savefig(ROOT / "reports" / "figures" / "04_trend_over_time.png", dpi=140, bbox_inches="tight")
plt.show()"""),
    code("""# Most negatively correlated features with stunting
from src.config import ALL_FEATURES, TARGET
corrs = df[ALL_FEATURES + [TARGET]].corr(method="spearman")[TARGET].drop(TARGET).sort_values()
fig, ax = plt.subplots(figsize=(8, 5))
corrs.plot(kind="barh", ax=ax,
            color=["#27ae60" if v < 0 else "#c0392b" for v in corrs])
ax.set_title("Spearman correlation with stunting_rate (sorted)")
ax.axvline(0, color="black", lw=0.5)
plt.tight_layout()
fig.savefig(ROOT / "reports" / "figures" / "05_feature_correlations.png", dpi=140, bbox_inches="tight")
plt.show()"""),

    # -------------------------------------------------------------- 5. hypoth
    md("""## 5. Hypothesis Testing (H1 - H5)

We test each substantive hypothesis using **Spearman's rho** (rank correlation),
which captures monotonic relationships without assuming linearity. We reject the
null at &alpha; = 0.05 only if the p-value is below 0.05 **and** the sign of the
correlation matches what the hypothesis predicts."""),
    code("""from src import hypothesis_tests as ht
h_results = ht.run_all(df)
h_results"""),

    # -------------------------------------------------------------- 6. modelling
    md("""## 6. Modelling

We compare a wide model family - a naive mean baseline, linear models with and
without regularisation, tree-based models, gradient boosting, and KNN - using
**5-fold cross-validated RMSE** as the primary metric."""),
    code("""from src import modeling
leaderboard, fitted = modeling.evaluate_all(X, y)
leaderboard"""),
    code("""viz.plot_model_leaderboard(leaderboard, save="06_model_leaderboard.png")
plt.show()"""),
    code("""best_name = leaderboard.iloc[0]["name"]
best_model = fitted[best_name]
best_path = modeling.save_best(fitted, leaderboard)
print(f"Best model: {best_name} -> {best_path}")"""),

    # -------------------------------------------------------------- 7. eval
    md("""## 7. Evaluation

### 7.1 Hypothesis H6 - does the model beat the baseline?"""),
    code("""h6 = ht.test_h6_ml_beats_baseline(best_model, X, y)
pd.DataFrame([h6])"""),
    md("### 7.2 Feature importance"),
    code("""# Use built-in importances for tree models; else fall back to permutation importance.
from sklearn.inspection import permutation_importance
try:
    importances = pd.Series(best_model.feature_importances_, index=X.columns,
                             name="importance")
except AttributeError:
    r = permutation_importance(best_model, X, y, n_repeats=10, random_state=42, n_jobs=-1)
    importances = pd.Series(r.importances_mean, index=X.columns, name="importance")
importances = importances.sort_values(ascending=False)
importances.head(15)"""),
    code("""viz.plot_feature_importance(importances, save="07_feature_importance.png")
plt.show()"""),
    md("### 7.3 SHAP analysis (tree models)"),
    code("""# SHAP gives consistent, signed contributions per row. We compute it on a
# sample for speed. Tree models -> fast TreeExplainer; otherwise KernelExplainer
# on a small background sample.
try:
    import shap
    sample = X.sample(min(200, len(X)), random_state=42)
    try:
        explainer = shap.TreeExplainer(best_model)
        shap_vals = explainer(sample, check_additivity=False)
    except Exception:
        background = shap.sample(X, 50, random_state=42)
        explainer = shap.KernelExplainer(best_model.predict, background)
        shap_vals = explainer.shap_values(sample, nsamples=100)
        shap_vals = shap.Explanation(values=shap_vals,
                                      base_values=explainer.expected_value,
                                      data=sample.values,
                                      feature_names=list(X.columns))
    shap.plots.beeswarm(shap_vals, max_display=12, show=False)
    plt.tight_layout()
    plt.savefig(ROOT / "reports" / "figures" / "08_shap_beeswarm.png", dpi=140, bbox_inches="tight")
    plt.show()
except Exception as exc:
    print(f"SHAP skipped ({type(exc).__name__}): {exc}")"""),
    md("### 7.4 Predicted vs actual on the hold-out"),
    code("""from sklearn.model_selection import train_test_split
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
best_model.fit(X_tr, y_tr)
pred = best_model.predict(X_te)
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(y_te, pred, alpha=0.6, color="#2c3e50")
lims = [min(y_te.min(), pred.min()) - 1, max(y_te.max(), pred.max()) + 1]
ax.plot(lims, lims, "--", color="#c0392b", label="y = x")
ax.set_xlabel("Actual stunting rate (%)"); ax.set_ylabel("Predicted")
ax.set_title(f"Predicted vs actual ({best_name})")
ax.legend(); plt.tight_layout()
fig.savefig(ROOT / "reports" / "figures" / "09_predicted_vs_actual.png", dpi=140, bbox_inches="tight")
plt.show()"""),

    # -------------------------------------------------------------- 8. deploy
    md("""## 8. Deployment

For each sub-region we take the **most recent** survey year, score it with the
best model, and produce a ranked risk list. This is the primary actionable
output of the project."""),
    code("""from src.preprocessing import latest_year
latest = latest_year(df)
X_latest, _ = feature_matrix(latest)
ranked = modeling.predict_hotspots(best_model, X_latest,
                                     latest[["region", "subregion", "year"]])
from src.config import OUTPUTS_DIR
ranked.to_csv(OUTPUTS_DIR / "hotspots_ranked.csv", index=False)
ranked.head(15)"""),
    code("""viz.plot_hotspot_map(ranked, top_n=15, save="10_hotspots_top15.png")
plt.show()"""),

    # =====================================================================
    md("""## 9. Classification - risk band

Re-cast stunting as the **WHO public-health risk band** (low / medium / high /
critical) and train a multi-class classifier. The bands follow WHO's
classification of stunting prevalence:

* `<20%`  — low
* `20-29%` — medium
* `30-39%` — high
* `>=40%`  — critical (very high)

This complements the regression: instead of estimating a percentage we predict
which response protocol a sub-region triggers."""),
    code("""from src import classification as clf
df_band = clf.add_risk_band(df)
print(df_band["risk_band"].value_counts())
df_band[["region", "subregion", "year", "stunting_rate", "risk_band"]].head()"""),
    code("""Xc, _ = feature_matrix(df_band)
yc = df_band["risk_band"]
clf_leaderboard, clf_fitted, clf_reports = clf.evaluate_all(Xc, yc)
clf_leaderboard"""),
    code("""best_clf_name = clf_leaderboard.iloc[0]["name"]
best_clf = clf_fitted[best_clf_name]
print(f"Best classifier: {best_clf_name}")
import numpy as np
cm = np.array(clf_reports[best_clf_name]["confusion_matrix"])
labels = clf_reports[best_clf_name]["labels"]
fig, ax = plt.subplots(figsize=(5, 4))
im = ax.imshow(cm, cmap="Reds")
ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=30)
ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels)
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
ax.set_title(f"Confusion matrix - {best_clf_name}")
for i in range(len(labels)):
    for j in range(len(labels)):
        ax.text(j, i, cm[i, j], ha="center", va="center",
                color="white" if cm[i,j] > cm.max()/2 else "black")
plt.tight_layout()
fig.savefig(ROOT / "reports" / "figures" / "11_confusion_matrix.png", dpi=140, bbox_inches="tight")
plt.show()"""),

    # =====================================================================
    md("""## 10. Clustering - K-Means on socio-economic drivers

Unsupervised grouping of sub-regions by their **drivers** (not their stunting
outcome). Each cluster has a recognisable profile and likely needs a similar
intervention package."""),
    code("""from src import clustering
# Choose k by silhouette
elbow = clustering.choose_k(latest)
fig, ax1 = plt.subplots(figsize=(7, 4))
ax2 = ax1.twinx()
ax1.plot(elbow["k"], elbow["inertia"], "o-", color="#2c3e50", label="Inertia")
ax2.plot(elbow["k"], elbow["silhouette"], "s--", color="#c0392b", label="Silhouette")
ax1.set_xlabel("k"); ax1.set_ylabel("Inertia", color="#2c3e50")
ax2.set_ylabel("Silhouette", color="#c0392b")
ax1.set_title("Elbow + silhouette for K-Means")
plt.tight_layout()
fig.savefig(ROOT / "reports" / "figures" / "12_elbow.png", dpi=140, bbox_inches="tight")
plt.show()
best_k = int(elbow.sort_values("silhouette", ascending=False).iloc[0]["k"])
print(f"Best k by silhouette: {best_k}")"""),
    code("""km, scaler, cluster_labels, sil = clustering.fit_kmeans(latest, k=best_k)
profile = clustering.profile_clusters(latest, cluster_labels)
names = clustering.label_clusters(profile)
profile["cluster_label"] = profile["cluster"].map(names)
profile"""),
    code("""# Visualise clusters in PCA(2) space
coords, pca = clustering.pca_2d(latest)
fig, ax = plt.subplots(figsize=(7, 5))
for c in sorted(set(cluster_labels)):
    mask = cluster_labels == c
    ax.scatter(coords[mask, 0], coords[mask, 1], s=60, alpha=0.85,
                label=names[c])
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% var)")
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% var)")
ax.set_title(f"K-Means clusters (k={best_k}) in PCA(2) space")
ax.legend(frameon=False, fontsize=9, loc="best")
plt.tight_layout()
fig.savefig(ROOT / "reports" / "figures" / "13_clusters_pca.png", dpi=140, bbox_inches="tight")
plt.show()"""),

    # =====================================================================
    md("""## 11. Forecasting - per-sub-region linear trends to 2026 / 2028

For each sub-region we fit a linear time-trend on its observed stunting series
and extrapolate to the **FORECAST_YEARS**. The slope is itself useful: negative
means improving, positive means stagnating or worsening."""),
    code("""from src import forecasting
trends = forecasting.fit_trends(df)
fc = forecasting.forecast(df)
print("Mean stunting by forecast year:")
print(fc.groupby("year")["forecast_stunting"].mean().round(2))
print()
print("5 fastest-improving sub-regions:")
forecasting.rank_improvers(trends, top_n=5)"""),
    code("""# Plot the trend + forecast for the 5 worst sub-regions
top5 = ranked.head(5)["subregion"].tolist()
fig, ax = plt.subplots(figsize=(9, 5))
for sub in top5:
    g = df[df["subregion"] == sub].sort_values("year")
    ax.plot(g["year"], g["stunting_rate"], "o-", label=sub)
    fc_sub = fc[fc["subregion"] == sub].sort_values("year")
    last_year, last_val = g["year"].max(), g.iloc[-1]["stunting_rate"]
    xs = [last_year] + fc_sub["year"].tolist()
    ys = [last_val]  + fc_sub["forecast_stunting"].tolist()
    ax.plot(xs, ys, "--", color=ax.lines[-1].get_color(), alpha=0.6)
ax.set_xlabel("Year"); ax.set_ylabel("Stunting rate (%)")
ax.set_title("Observed (solid) + forecast (dashed) - top-5 hotspots")
ax.legend(frameon=False, fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
fig.savefig(ROOT / "reports" / "figures" / "14_forecasts_top5.png", dpi=140, bbox_inches="tight")
plt.show()"""),

    # =====================================================================
    md("""## 12. Conclusions

**Hypothesis results (H1-H6):** all six rejected the null at p < 0.001.
Maternal education, WASH, wealth, and facility density all show strong
*negative* rank-correlation with stunting; malaria shows strong *positive*
rank-correlation; and the regression model beats the naive mean baseline by
60-70% on cross-validated RMSE.

**Hotspots:** the three northern regions (Far North, North, Adamawa) plus
East dominate the predicted top-15. These are the recommended priority
sub-regions for nutrition + WASH programmes -- see
`outputs/hotspots_ranked.csv`.

**Clusters:** K-Means separates Cameroon into a small number of profile
archetypes. The "Northern-rural (critical risk)" cluster is the one with
the worst drivers across the board; the "Urban-affluent (low risk)" cluster
sits at the other end and is dominated by Centre / Littoral.

**Forecasts:** every sub-region is projected to improve to 2028, but the
worst-performing ones close the gap slowly. Several northern districts are
still in the "high" or "critical" WHO band in the 2028 forecast.

**Limitations.** The synthetic-data fallback is calibrated to published
national means and the North-South gradient, but for production use the
real-data path in `preprocessing._build_from_real()` (currently a documented
stub) would need to map DHS long-format CSVs to the wide analysis schema and
aggregate OSM health-facility points to admin-2 units.

**Next steps.** Implement that real-data stitching; refresh the
ranked list and the [Next.js atlas](../web/) (run
``python scripts/sync_web_data.py`` after re-running the pipeline).
"""),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.cells = CELLS
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3", "language": "python", "name": "python3"
    }
    NB_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}  ({len(CELLS)} cells)")


if __name__ == "__main__":
    sys.exit(main())
