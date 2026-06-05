# Cameroon Malnutrition Atlas

**Course:** CEC 420 — Data Mining
**Author:** SEPO PERRY-BRADLEY DINGA (CT23A145)
**Department:** Computer Engineering — Software Engineering, University of Buea
**Academic Year:** 2025 / 2026

A CRISP-DM project that identifies the strongest drivers of child stunting in
Cameroon and produces a ranked list of high-risk regions using **real DHS &
MICS sub-national data** from 1991–2018 (the only public sub-national survey
series Cameroon has released). Four data-mining techniques are applied:

| Technique       | What it answers                                                                  |
|-----------------|-----------------------------------------------------------------------------------|
| **Regression**      | What's the predicted stunting % for each region?                              |
| **Classification**  | Which WHO risk band (low / medium / high / critical) does each region fall in?|
| **Clustering**      | Which regions share a similar driver profile?                                 |
| **Forecasting**     | Where will each region be in 2026 / 2028 if its trend continues?              |

Plus an **in-browser predictor** (the `/predict` page) — exported linear, logistic
and K-Means models that run client-side with no backend.

## Real data, not synthetic

The pipeline uses **only real Cameroon DHS / MICS values**:

- Sub-national stunting + 13 driver features for **10 regions × 5 DHS rounds = 50 rows**.
- Survey years: **1991, 1998, 2004, 2011, 2018**.
- 1991/1998 only published five mega-regions (e.g. "Adamaoua/Nord/Extrême-Nord");
  we broadcast each mega value to its constituent modern regions so the time
  series is complete.
- No newer sub-national survey for Cameroon exists in the public domain yet;
  forecasts to 2026/2028 are linear extrapolations from this real series.

There is no synthetic-data fallback any more.

## Quick start

```powershell
# 1. Install Python dependencies (Python 3.11)
& "C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe" -m pip install -r requirements.txt

# 2. Download HDX data (one-time, ~100 CSVs, mostly DHS Cameroon)
& "C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe" scripts\download_data.py

# 3. Run the full pipeline (4 techniques + hypotheses + deployable models)
& "C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe" scripts\run_pipeline.py

# 4. Build + execute the analysis notebook
& "C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe" scripts\build_notebook.py
jupyter notebook notebooks\malnutrition_analysis.ipynb

# 5. Sync data + start the webapp
& "C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe" scripts\sync_web_data.py
cd web
npm install --legacy-peer-deps
npm run dev          # http://localhost:3000
```

## Repository layout

```
data420/
|-- data/
|   |-- raw/                HDX downloads
|   `-- processed/          cameroon_subregional.csv (50 rows × 17 cols)
|-- src/
|   |-- config.py           survey years, regions, feature groups
|   |-- data_loader.py      HDX CKAN downloader
|   |-- dhs_loader.py       REAL DHS/MICS long-format -> wide-format stitcher
|   |-- preprocessing.py    join + clean + impute (no synthetic fallback)
|   |-- features.py         engineered features (WASH composite, etc.)
|   |-- modeling.py         regression model zoo + 5-fold CV
|   |-- classification.py   WHO risk-band classifier
|   |-- clustering.py       K-Means + silhouette
|   |-- forecasting.py      per-region trend extrapolation
|   |-- hypothesis_tests.py H1-H6 (Spearman + paired t-test)
|   |-- deployable.py       exports trained linear/logistic/k-means to JSON
|   `-- visualization.py    plotting helpers
|-- notebooks/
|   `-- malnutrition_analysis.ipynb   CRISP-DM walkthrough on real data
|-- scripts/
|   |-- download_data.py
|   |-- run_pipeline.py
|   |-- build_notebook.py
|   |-- inspect_dhs.py      one-off: maps DHS indicators to features
|   `-- sync_web_data.py    converts outputs/ to JSON for the webapp
|-- web/                    Next.js 16 + Tailwind 4 + TypeScript webapp
|   |-- app/
|   |   |-- page.tsx                Home: hero, KPIs, H1-H6 strip, top hotspots
|   |   |-- predict/page.tsx        In-browser what-if predictor
|   |   |-- hotspots/page.tsx       Choropleth + ranked region list
|   |   |-- regression/page.tsx     Model leaderboard + chart
|   |   |-- classification/page.tsx Confusion matrix + per-class metrics
|   |   |-- clustering/page.tsx     Cluster profiles + silhouette
|   |   |-- forecasts/page.tsx      Per-region trend + 2026/2028 projections
|   |   |-- hypotheses/page.tsx     H1-H6 cards
|   |   |-- data/page.tsx           Filterable data explorer
|   |   |-- about/page.tsx          Methodology, feature map, sources
|   |   `-- region/[name]/page.tsx  Drill-down per region
|   |-- components/                 Card, KpiTile, DataTable, ChoroplethMap,
|   |                                BarChart, ConfusionMatrix, Predictor,
|   |                                HypothesisStrip, DataBanner
|   |-- lib/                        types, data loaders, formatters, predict.ts
|   `-- public/data/                JSON payloads + Cameroon admin-1 GeoJSON
|-- reports/
|   |-- figures/                    PNG plots saved by the notebook
|   `-- final_report.md             final write-up
|-- models/                         best_model.joblib
|-- outputs/                        all pipeline CSVs + classifier_reports.json + predictor.json
`-- requirements.txt
```

## Hypotheses

All six are tested on the real DHS series.

| ID  | Statement                                                                              | Method            |
|-----|----------------------------------------------------------------------------------------|-------------------|
| H1  | Maternal education (% women secondary+) is negatively associated with stunting         | Spearman ρ        |
| H2  | Improved water + sanitation are negatively associated with stunting                    | Spearman ρ on WASH composite |
| H3  | Socio-economic status proxy (literacy + secondary edu) is negatively associated        | Spearman ρ        |
| H4  | Healthcare access (% births in health facility) is negatively associated               | Spearman ρ        |
| H5  | Malaria prevalence is positively associated with stunting                              | Spearman ρ        |
| H6  | The ML regression beats the mean-baseline on cross-validated RMSE at α=0.05            | one-sided paired t-test |

Run `outputs/hypothesis_tests.csv` for the latest numbers — all six are
supported on the real data.

## The in-browser predictor

`scripts/run_pipeline.py` finishes by exporting `outputs/predictor.json` — a
~10 KB bundle containing:

- Standardised **Linear Regression** (coefficients + scaler params) for stunting %
- Standardised multinomial **Logistic Regression** for the WHO risk band
- Standardised **K-Means** centroids for cluster assignment
- Min/max/median per feature for the slider bounds

The webapp's `/predict` page imports this JSON and runs inference entirely
client-side from `web/lib/predict.ts` — no backend, no API calls.
