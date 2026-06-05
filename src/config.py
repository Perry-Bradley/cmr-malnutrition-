"""Project paths and constants."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

for d in (RAW_DIR, INTERIM_DIR, PROCESSED_DIR, MODELS_DIR, OUTPUTS_DIR, FIGURES_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Survey years used for this project (REAL Cameroon DHS rounds).
# These are the only years for which sub-national stunting data has been
# published publicly. The next DHS-VI Cameroon round was anticipated 2024 but
# had not been released at the time of this analysis.
SURVEY_YEARS = [1991, 1998, 2004, 2011, 2018]
DHS_SURVEY_YEARS = SURVEY_YEARS  # backwards-compat alias

# Years for which we will forecast stunting from the trend.
FORECAST_YEARS = [2026, 2028]

# Risk-band thresholds for the classification task.
# Aligned with WHO classification of public-health significance for stunting:
#   <20% low | 20-29% medium | 30-39% high | >=40% critical (very high)
RISK_BAND_BINS   = [-0.1, 20, 30, 40, 101]
RISK_BAND_LABELS = ["low", "medium", "high", "critical"]

# Cameroon's 10 administrative regions
CAMEROON_REGIONS = [
    "Adamawa", "Centre", "East", "Far North", "Littoral",
    "North", "Northwest", "South", "Southwest", "West",
]

# HDX dataset identifiers (used by the CKAN API)
HDX_DATASETS = {
    "dhs_subnational": "dhs-subnational-data-for-cameroon",
    "who_indicators":  "who-data-for-cmr",
    "health_facilities": "hotosm_cmr_health_facilities",
    "population_density": "highresolutionpopulationdensitymaps-cmr",
    "admin_boundaries": "cod-ab-cmr",
}

# Target variable
TARGET = "stunting_rate"

# Feature groups used in modelling -- all sourced from real DHS / MICS CSVs.
FEATURE_GROUPS = {
    "maternal_education": ["women_secondary_plus_pct", "women_literate_pct"],
    "wash":               ["improved_water_pct", "improved_sanitation_pct"],
    "healthcare":         ["antenatal_4plus_pct", "antenatal_skilled_pct",
                            "skilled_birth_attendance_pct",
                            "health_facility_delivery_pct",
                            "health_insurance_any_pct"],
    "disease":            ["malaria_prevalence_pct", "child_anemia_pct"],
    "nutrition_siblings": ["wasting_pct", "underweight_pct"],
    "demographic":        ["fertility_rate"],
}

ALL_FEATURES = [f for group in FEATURE_GROUPS.values() for f in group]
