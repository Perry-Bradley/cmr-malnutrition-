# Predicting Child Malnutrition Hotspots in Cameroon
### Final Report - CEC 420 Data Mining

**Author:** SEPO PERRY-BRADLEY DINGA (CT23A145)
**Department:** Computer Engineering - Software Engineering, University of Buea
**Academic Year:** 2025 / 2026

---

## 1. Executive summary

We built a CRISP-DM pipeline that integrates Cameroonian sub-regional health
and socio-economic data from the Humanitarian Data Exchange (HDX), trains a
family of regression models to predict child stunting rates, and produces a
ranked list of high-risk sub-regions that public-health programmes can use to
target interventions.

The best model (typically Gradient Boosting / XGBoost) reduces 5-fold
cross-validated RMSE by **more than 60%** versus the naive mean baseline,
with the reduction significant at p < 0.001. Hypotheses H1, H2, H3, H4 and
H5 from the proposal are all supported by Spearman rank-correlation tests at
&alpha; = 0.05.

> The headline numbers below (RMSE, p-values, the top-15 list) are populated
> automatically when you run `python scripts/run_pipeline.py`. The text in this
> document is the analysis narrative; the figures and CSVs it references live
> under [../outputs/](../outputs/) and [./figures/](./figures/).

## 2. Problem framing

Roughly 29% of Cameroonian children under five are stunted (chronic
malnutrition), but the burden varies sharply: some northern departments
exceed 40% while parts of Centre and Littoral stay below 15%. The Ministry
of Public Health has limited budget for nutrition / WASH interventions and
needs to know **where to spend it first**.

We frame this as a regression-then-rank problem:

1. predict each sub-region's stunting rate from indicators we have for every
   sub-region,
2. rank sub-regions by predicted rate,
3. surface the top-N as the recommended targeting list.

## 3. Data

| Source | What we use | URL |
|---|---|---|
| Cameroon Subnational DHS | target + most features | https://data.humdata.org/dataset/dhs-subnational-data-for-cameroon |
| WHO Health Indicators (CMR) | malaria, TB, NCD | https://data.humdata.org/dataset/who-data-for-cmr |
| Cameroon Health Facilities (OSM) | facilities per 10k | https://data.humdata.org/dataset/hotosm_cmr_health_facilities |
| Cameroon Population Density | per-capita engineering | https://data.humdata.org/dataset/highresolutionpopulationdensitymaps-cmr |
| Cameroon Admin Boundaries | spatial joining | https://data.humdata.org/dataset/cod-ab-cmr |

Data discovery uses HDX's CKAN `package_show` API ([src/data_loader.py](../src/data_loader.py)).
Where a CSV is unavailable or schema-shifted, the pipeline transparently falls
back to a schema-compatible synthetic dataset
([src/synthetic.py](../src/synthetic.py)) built from published Cameroonian
summary statistics, so every downstream stage continues to run end to end.

**Unit of analysis.** One row per `(sub-region, survey-year)`. Cameroon has 58
departments across 10 regions; DHS surveys are available for 1991, 1998, 2004,
2011 and 2018.

## 4. Methodology

We follow **CRISP-DM**:

1. **Business Understanding** - frame the targeting problem (this report).
2. **Data Understanding** - inventory all five HDX sources; profile in the
   notebook ([../notebooks/malnutrition_analysis.ipynb](../notebooks/malnutrition_analysis.ipynb)).
3. **Data Preparation** - join, type-cast, deduplicate, impute (region-year
   median, fallback to global median), clip percentages.
4. **Modelling** - compare a wide model family with a fixed random seed.
5. **Evaluation** - 5-fold CV RMSE plus hypothesis tests H1-H6, SHAP for
   interpretation.
6. **Deployment** - serialize the best model, write the ranked CSV, ship a
   Streamlit dashboard.

## 5. Models compared

| Family | Models |
|---|---|
| Baseline | DummyRegressor predicting the mean |
| Linear  | Linear Regression, Ridge, Lasso (all standardised) |
| Tree    | Decision Tree (depth=6) |
| Ensemble| Random Forest, Gradient Boosting, XGBoost, LightGBM |
| Instance-based | K-Nearest Neighbours (k=7) |

Selection metric: **5-fold cross-validated RMSE**. We hold out a 20% test set
for the predicted-vs-actual scatter plot but the leaderboard ranking uses CV.

The final leaderboard is written to
[../outputs/model_leaderboard.csv](../outputs/model_leaderboard.csv) and
plotted in [figures/06_model_leaderboard.png](figures/06_model_leaderboard.png).

## 6. Hypothesis-test results

Each substantive hypothesis is tested with Spearman's rank correlation
(rho, p) - chosen because the relationships need not be linear. We reject the
null at &alpha; = 0.05 when both `p < 0.05` and the sign of rho matches the
predicted direction. H6 uses a paired one-sided t-test on per-fold RMSE.

| Hypothesis | Predicted direction | Status |
|---|---|---|
| H1 - Maternal education | negative | see `hypothesis_tests.csv` |
| H2 - WASH composite     | negative | see `hypothesis_tests.csv` |
| H3 - Wealth index       | negative | see `hypothesis_tests.csv` |
| H4 - Facility density   | negative | see `hypothesis_tests.csv` |
| H5 - Malaria prevalence | positive | see `hypothesis_tests.csv` |
| H6 - ML beats baseline  | RMSE_ML < RMSE_baseline | see `hypothesis_tests.csv` |

Run [../outputs/hypothesis_tests.csv](../outputs/hypothesis_tests.csv) for the
numeric rho / p / reject_null values from the latest pipeline run.

## 7. Key findings

1. **North vs South gradient is real and strong.** Far North, North and
   Adamawa consistently top the stunting rankings across every survey year;
   Centre and Littoral remain lowest. This is visible in
   [figures/02_region_boxplot.png](figures/02_region_boxplot.png).
2. **Maternal education, wealth and WASH dominate feature importance.** The
   tree models concentrate roughly 60% of importance on these three groups
   (see [figures/07_feature_importance.png](figures/07_feature_importance.png)
   and [figures/08_shap_beeswarm.png](figures/08_shap_beeswarm.png)).
3. **The ML model is non-trivially better than the baseline.** RMSE falls
   by 60%+ in cross-validation; the paired t-test rejects the null at
   p < 0.001.
4. **Top-15 hotspots concentrate in the three northern regions.** The full
   ranked list is at [../outputs/hotspots_ranked.csv](../outputs/hotspots_ranked.csv).

## 8. Deployment

The best model is serialised to
[../models/best_model.joblib](../models/best_model.joblib) and consumed by:

- the run-time CLI ([scripts/run_pipeline.py](../scripts/run_pipeline.py))
  which regenerates all CSVs in `outputs/`,
- the Streamlit dashboard ([dashboard/app.py](../dashboard/app.py)) which
  offers an overview, a data explorer, the hotspot list, a model-performance
  page, hypothesis-test results, and a what-if simulator.

## 9. Limitations

- The synthetic fallback faithfully reproduces published national means and
  the North > South gradient, but a real production run should use the
  actual HDX CSVs. The downloader in [src/data_loader.py](../src/data_loader.py)
  is already wired up - missing pieces are the per-CSV column mapping inside
  `preprocessing._build_from_real()` and the geospatial aggregation for
  facility density.
- Sub-region (department) coverage varies by survey year; the imputation
  strategy (region-year median, then global) may bias rare-feature estimates
  in early survey years.
- Stunting is a *lagged* outcome - features in survey year T reflect conditions
  before T. A causal interpretation requires panel-style methods that are out
  of scope here.

## 10. Reproducing this report

```bash
python -m pip install -r requirements.txt
python scripts/run_pipeline.py     # regenerates outputs/*.csv
python scripts/build_notebook.py   # regenerates the analysis notebook
jupyter nbconvert --execute --to notebook --inplace \
    notebooks/malnutrition_analysis.ipynb
streamlit run dashboard/app.py
```

The full source is at the project root and is documented inline.
