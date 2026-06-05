// Server-side data loaders. Each function reads a JSON file from
// `public/data/` (produced by scripts/sync_web_data.py) and returns a typed
// payload. Safe to call from Server Components / page() functions.

import { promises as fs } from "node:fs";
import path from "node:path";
import type {
  ClassificationReport, ClassifierLeaderboardRow, ClusterAssignment,
  ClusterProfile, ElbowRow, ForecastRow, Hotspot, HypothesisRow,
  LeaderboardRow, PredictorPayload, RegionAgg, Subregion, Summary, TrendRow,
} from "./types";

const DATA_DIR = path.join(process.cwd(), "public", "data");

async function readJson<T>(name: string): Promise<T> {
  const raw = await fs.readFile(path.join(DATA_DIR, name), "utf-8");
  return JSON.parse(raw) as T;
}

export const getSummary       = () => readJson<Summary>("summary.json");
export const getSubregional   = () => readJson<Subregion[]>("subregional.json");
export const getHotspots      = () => readJson<Hotspot[]>("hotspots.json");
export const getLeaderboard   = () => readJson<LeaderboardRow[]>("leaderboard.json");
export const getHypotheses    = () => readJson<HypothesisRow[]>("hypotheses.json");
export const getRegionAgg     = () => readJson<RegionAgg[]>("regions.json");
export const getClassifierLB  = () => readJson<ClassifierLeaderboardRow[]>("classifier_leaderboard.json");
export const getClassifierReports = () => readJson<Record<string, ClassificationReport>>("classifier_reports.json");
export const getClusterProfiles   = () => readJson<ClusterProfile[]>("cluster_profiles.json");
export const getClusterAssignments = () => readJson<ClusterAssignment[]>("cluster_assignments.json");
export const getElbow         = () => readJson<ElbowRow[]>("cluster_elbow.json");
export const getTrends        = () => readJson<TrendRow[]>("trends.json");
export const getForecasts     = () => readJson<ForecastRow[]>("forecasts.json");
export const getPredictor     = () => readJson<PredictorPayload>("predictor.json");

// Cameroon admin-1 GeoJSON region name -> our canonical region name.
export const GEO_REGION_MAP: Record<string, string> = {
  "Adamaoua":   "Adamawa",
  "North-West": "Northwest",
  "South-West": "Southwest",
};

export function normaliseRegion(name: string): string {
  return GEO_REGION_MAP[name] ?? name;
}
