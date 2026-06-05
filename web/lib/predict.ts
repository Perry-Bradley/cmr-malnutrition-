// Client-side inference: same math as the exported Python models.

import type {
  KMeansSpec, LinRegSpec, LogRegSpec, PredictorPayload,
} from "./types";

export type FeatureVector = Record<string, number>;

/** Order + standardise an input vector to match the model's training space. */
function standardise(spec: { features: string[]; scaler_mean: number[]; scaler_scale: number[] },
                      x: FeatureVector): number[] {
  return spec.features.map((f, i) => {
    const v = x[f] ?? spec.scaler_mean[i];      // fall back to mean if missing
    const s = spec.scaler_scale[i] || 1;
    return (v - spec.scaler_mean[i]) / s;
  });
}

export function predictStunting(spec: LinRegSpec, x: FeatureVector): number {
  const z = standardise(spec, x);
  const dot = z.reduce((acc, zi, i) => acc + zi * spec.coef[i], 0);
  const v = dot + spec.intercept;
  return Math.max(0, Math.min(100, v));
}

export function predictRiskBand(spec: LogRegSpec, x: FeatureVector): {
  label: string;
  probabilities: Array<{ label: string; p: number }>;
} {
  const z = standardise(spec, x);
  const logits = spec.classes.map((_, k) => {
    const dot = z.reduce((acc, zi, i) => acc + zi * spec.coef[k][i], 0);
    return dot + spec.intercept[k];
  });
  const max = Math.max(...logits);
  const exps = logits.map((l) => Math.exp(l - max));
  const sum = exps.reduce((a, b) => a + b, 0);
  const probs = exps.map((e) => e / sum);
  let bestIdx = 0;
  probs.forEach((p, i) => { if (p > probs[bestIdx]) bestIdx = i; });
  return {
    label: spec.classes[bestIdx],
    probabilities: spec.classes.map((c, i) => ({ label: c, p: probs[i] })),
  };
}

export function nearestCluster(spec: KMeansSpec, x: FeatureVector): {
  cluster: number;
  distance: number;
} {
  const z = standardise(spec, x);
  let bestK = 0, bestD = Infinity;
  spec.centroids.forEach((c, k) => {
    let d = 0;
    for (let i = 0; i < z.length; i++) { const r = z[i] - c[i]; d += r * r; }
    if (d < bestD) { bestD = d; bestK = k; }
  });
  return { cluster: bestK, distance: Math.sqrt(bestD) };
}

export function predictAll(payload: PredictorPayload, x: FeatureVector) {
  return {
    stunting: predictStunting(payload.regression, x),
    band:     predictRiskBand(payload.classification, x),
    cluster:  nearestCluster(payload.clustering, x),
  };
}
