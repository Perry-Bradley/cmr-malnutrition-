// Type definitions matching the JSON payloads written by scripts/sync_web_data.py.
// Note: with the switch to real DHS data the unit of analysis is the
// 10 Cameroon admin-1 regions; the `subregion` column equals `region`.

export type Summary = {
  n_regions: number;
  n_subregions: number;
  survey_years: number[];
  latest_year: number;
  national_mean_stunting: number;
  worst_subregion_pct: number;
  best_subregion_pct: number;
  best_model: string;
  best_cv_rmse: number;
  baseline_cv_rmse: number;
  improvement_pct: number | null;
  n_hypotheses_supported: number;
  n_hypotheses_total: number;
};

export type Subregion = {
  region: string;
  subregion: string;
  year: number;
  breakdown_dim?: string;
  breakdown_value?: string;
  stunting_rate: number;
  wasting_pct: number;
  underweight_pct: number;
  child_anemia_pct: number;
  women_secondary_plus_pct: number;
  women_literate_pct: number;
  improved_water_pct: number;
  improved_sanitation_pct: number;
  antenatal_4plus_pct: number;
  antenatal_skilled_pct: number;
  skilled_birth_attendance_pct: number;
  health_facility_delivery_pct: number;
  health_insurance_any_pct: number;
  malaria_prevalence_pct: number;
  fertility_rate: number;
};

export type Hotspot = {
  rank: number;
  region: string;
  subregion: string;
  year: number;
  predicted_stunting: number;
  predicted_band?: string;
  cluster?: number;
  cluster_label?: string;
  forecast_2026?: number;
  forecast_2028?: number;
};

export type LeaderboardRow = {
  name: string;
  rmse: number;
  mae: number;
  r2: number;
  cv_rmse_mean: number;
  cv_rmse_std: number;
};

export type HypothesisRow = {
  hypothesis: string;
  feature: string | null;
  expected_sign: string | null;
  rho: number | null;
  p_value: number;
  n: number | null;
  reject_null: boolean;
  ml_rmse_mean?: number | null;
  baseline_rmse_mean?: number | null;
  improvement_pct?: number | null;
  t_stat?: number | null;
};

export type RegionAgg = {
  region: string;
  predicted_stunting_mean: number;
  predicted_stunting_max: number;
  n_subregions: number;
};

export type ClassifierLeaderboardRow = {
  name: string;
  accuracy: number;
  macro_f1: number;
  cv_accuracy_mean: number;
  cv_accuracy_std: number;
};

export type ClassificationReport = {
  confusion_matrix: number[][];
  classification_report: Record<string, Record<string, number> | number>;
  labels: string[];
};

export type ClusterProfile = {
  cluster: number;
  cluster_label: string;
  n_subregions: number;
  stunting_rate: number;
  [feature: string]: number | string;
};

export type ClusterAssignment = {
  region: string;
  subregion: string;
  year: number;
  cluster: number;
  cluster_label: string;
  stunting_rate: number;
};

export type ElbowRow = { k: number; inertia: number; silhouette: number };

export type TrendRow = {
  region: string;
  subregion: string;
  slope_pp_per_year: number;
  intercept: number;
  r2: number;
  last_observed: number;
  last_year: number;
};

export type ForecastRow = {
  region: string;
  subregion: string;
  year: number;
  forecast_stunting: number;
  slope_pp_per_year: number;
  trend_r2: number;
};

// ---- Deployable model payload (predictor.json) ----

export type LinRegSpec = {
  features: string[];
  scaler_mean: number[];
  scaler_scale: number[];
  coef: number[];
  intercept: number;
  target_min: number;
  target_max: number;
};

export type LogRegSpec = {
  features: string[];
  scaler_mean: number[];
  scaler_scale: number[];
  classes: string[];
  coef: number[][];      // (n_classes, n_features)
  intercept: number[];   // (n_classes,)
};

export type KMeansSpec = {
  features: string[];
  scaler_mean: number[];
  scaler_scale: number[];
  centroids: number[][];  // (k, n_features)
};

export type FeatureRange = { min: number; max: number; median: number };

export type PredictorPayload = {
  regression:     LinRegSpec;
  classification: LogRegSpec;
  clustering:     KMeansSpec;
  risk_bands:     string[];
  feature_ranges: Record<string, FeatureRange>;
};
