"use client";

import { useMemo, useState } from "react";
import { RefreshCcw, Target, Users, GraduationCap, Droplets, Heart, Bug } from "lucide-react";
import type { PredictorPayload, Subregion } from "@/lib/types";
import { predictAll } from "@/lib/predict";
import { KpiTile } from "./KpiTile";
import { RiskBandBadge } from "./Badge";
import { Card } from "./Card";
import { cn, num, pct } from "@/lib/format";

const FEATURE_LABELS: Record<string, string> = {
  women_secondary_plus_pct:     "Women with secondary+ education",
  women_literate_pct:           "Women who are literate",
  improved_water_pct:           "Improved water access",
  improved_sanitation_pct:      "Improved sanitation",
  antenatal_4plus_pct:          "Antenatal visits 4+",
  antenatal_skilled_pct:        "Antenatal from skilled provider",
  skilled_birth_attendance_pct: "Skilled birth attendance",
  health_facility_delivery_pct: "Health facility delivery",
  health_insurance_any_pct:     "Any health insurance",
  malaria_prevalence_pct:       "Malaria prevalence (RDT)",
  child_anemia_pct:             "Under-5 anaemia",
  wasting_pct:                  "Under-5 wasting",
  underweight_pct:              "Under-5 underweight",
  fertility_rate:               "Total fertility rate (15–49)",
  // engineered (auto-computed, not shown)
};

const FEATURE_UNIT: Record<string, string> = {
  fertility_rate: " children/woman",
};
const FEATURE_STEP: Record<string, number> = {
  fertility_rate: 0.05,
};

// Group sliders by category for visual hierarchy.
const GROUPS: { id: string; label: string; icon: React.ReactNode; tone: string; features: string[] }[] = [
  { id: "edu",   label: "Education", icon: <GraduationCap className="h-3.5 w-3.5" />, tone: "bg-blue-50 text-blue-700",
    features: ["women_secondary_plus_pct", "women_literate_pct"] },
  { id: "wash",  label: "WASH",      icon: <Droplets className="h-3.5 w-3.5" />,        tone: "bg-cyan-50 text-cyan-700",
    features: ["improved_water_pct", "improved_sanitation_pct"] },
  { id: "care",  label: "Healthcare access", icon: <Heart className="h-3.5 w-3.5" />,   tone: "bg-rose-50 text-rose-700",
    features: ["antenatal_4plus_pct", "antenatal_skilled_pct", "skilled_birth_attendance_pct",
                "health_facility_delivery_pct", "health_insurance_any_pct"] },
  { id: "dis",   label: "Disease burden", icon: <Bug className="h-3.5 w-3.5" />,        tone: "bg-amber-50 text-amber-700",
    features: ["malaria_prevalence_pct", "child_anemia_pct", "wasting_pct", "underweight_pct"] },
  { id: "dem",   label: "Demographics", icon: <Users className="h-3.5 w-3.5" />,        tone: "bg-zinc-100 text-zinc-700",
    features: ["fertility_rate"] },
];

type Props = {
  payload: PredictorPayload;
  subregions: Subregion[];
};

export default function Predictor({ payload, subregions }: Props) {
  const inputFeatures = payload.regression.features.filter(
    (f) => f in payload.feature_ranges && FEATURE_LABELS[f] !== undefined,
  );

  const initial: Record<string, number> = useMemo(() => {
    const o: Record<string, number> = {};
    inputFeatures.forEach((f) => {
      o[f] = Math.round((payload.feature_ranges[f]?.median ?? 0) * 100) / 100;
    });
    return o;
  }, [payload, inputFeatures]);

  const [vals, setVals] = useState<Record<string, number>>(initial);
  const [preset, setPreset] = useState<string>("custom");

  const result = predictAll(payload, vals);

  function setVal(f: string, v: number) {
    setVals((cur) => ({ ...cur, [f]: v }));
    setPreset("custom");
  }

  function applyPreset(name: string) {
    if (name === "custom") return;
    if (name === "median") {
      setVals(initial);
      setPreset(name);
      return;
    }
    const [, yearStr, dim, sub] = name.split("|");
    const m = subregions.find(
      (r) => String(r.year) === yearStr
          && (r.breakdown_dim ?? "Region") === dim
          && r.subregion === sub,
    );
    if (!m) return;
    const next: Record<string, number> = { ...vals };
    inputFeatures.forEach((f) => {
      if (f in m) next[f] = Number((m as unknown as Record<string, number>)[f]);
    });
    setVals(next);
    setPreset(name);
  }

  const similar = useMemo(() => {
    const fs = payload.regression.features;
    const mean = payload.regression.scaler_mean;
    const scale = payload.regression.scaler_scale;
    const z0 = fs.map((f, i) => ((vals[f] ?? mean[i]) - mean[i]) / (scale[i] || 1));
    const scored = subregions.map((r) => {
      const z = fs.map((f, i) => {
        const v = (r as unknown as Record<string, number>)[f] ?? mean[i];
        return (v - mean[i]) / (scale[i] || 1);
      });
      let d = 0;
      for (let i = 0; i < z.length; i++) { const x = z[i] - z0[i]; d += x * x; }
      return { row: r, distance: Math.sqrt(d) };
    });
    return scored.sort((a, b) => a.distance - b.distance).slice(0, 5);
  }, [vals, payload, subregions]);

  const presetOptions = useMemo(() => {
    const sorted = [...subregions].sort((a, b) => {
      if (b.year !== a.year) return b.year - a.year;
      const da = a.breakdown_dim ?? "Region";
      const db = b.breakdown_dim ?? "Region";
      if (da !== db) return da.localeCompare(db);
      return a.subregion.localeCompare(b.subregion);
    });
    return [
      { value: "custom", label: "Custom (sliders)" },
      { value: "median", label: "National median" },
      ...sorted.map((s) => {
        const dim = s.breakdown_dim ?? "Region";
        const label = dim === "Region"
          ? `${s.subregion} · region · ${s.year}`
          : `${dim}: ${s.subregion} · ${s.year}`;
        return { value: `p|${s.year}|${dim}|${s.subregion}`, label };
      }),
    ];
  }, [subregions]);

  // Per-feature visual cue: where the current value sits in the range (0..1)
  function rangePos(f: string): number {
    const r = payload.feature_ranges[f];
    if (!r || r.max === r.min) return 0.5;
    return Math.max(0, Math.min(1, (vals[f] - r.min) / (r.max - r.min)));
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.05fr]">
      {/* ---------- left: inputs ---------- */}
      <Card
        title="Driver profile"
        subtitle="Move the sliders or pick a real DHS sub-population. Predictions update live."
        right={
          <div className="flex items-center gap-2">
            <select
              value={preset}
              onChange={(e) => applyPreset(e.target.value)}
              className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-xs max-w-[180px] truncate"
            >
              {presetOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => applyPreset("median")}
              className="inline-flex items-center gap-1 rounded-md border border-zinc-300 bg-white px-2 py-1 text-xs text-zinc-700 hover:bg-zinc-50"
              title="Reset to national median"
            >
              <RefreshCcw className="h-3 w-3" /> Reset
            </button>
          </div>
        }
      >
        <div className="flex flex-col gap-5">
          {GROUPS.map((g) => {
            const feats = g.features.filter((f) => inputFeatures.includes(f));
            if (!feats.length) return null;
            return (
              <fieldset key={g.id}>
                <legend className={cn(
                  "mb-2 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wider",
                  g.tone,
                )}>
                  {g.icon}{g.label}
                </legend>
                <div className="grid gap-3 sm:grid-cols-2">
                  {feats.map((f) => {
                    const r = payload.feature_ranges[f];
                    const step = FEATURE_STEP[f] ?? 0.1;
                    const unit = FEATURE_UNIT[f] ?? "";
                    return (
                      <label key={f} className="group flex flex-col gap-1.5 rounded-lg border border-zinc-200 bg-zinc-50/60 p-3 transition-colors hover:bg-white hover:border-zinc-300">
                        <div className="flex items-baseline justify-between gap-2">
                          <span className="text-xs text-zinc-700 leading-tight">{FEATURE_LABELS[f] ?? f}</span>
                          <span className="tabular-nums text-sm font-semibold text-zinc-900">
                            {num(vals[f] ?? 0, f === "fertility_rate" ? 2 : 1)}{unit}
                          </span>
                        </div>
                        <input
                          type="range"
                          min={r.min}
                          max={r.max}
                          step={step}
                          value={vals[f] ?? r.median}
                          onChange={(e) => setVal(f, Number(e.target.value))}
                          className="w-full"
                        />
                        <div className="flex justify-between text-[10px] text-zinc-400 tabular-nums">
                          <span>{num(r.min, 1)}</span>
                          <span className="text-zinc-300">·</span>
                          <span>{num(r.max, 1)}</span>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </fieldset>
            );
          })}
        </div>
      </Card>

      {/* ---------- right: predictions ---------- */}
      <div className="flex flex-col gap-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <KpiTile
            icon={<Target className="h-3.5 w-3.5" />}
            label="Predicted stunting"
            value={pct(result.stunting, 1)}
            hint="from linear-regression on 220 real DHS rows"
            tone={result.stunting >= 30 ? "danger" : result.stunting >= 20 ? "warning" : "good"}
          />
          <KpiTile
            label="Risk band"
            value={<RiskBandBadge band={result.band.label} />}
            hint={`confidence p=${num(result.band.probabilities.find((p) => p.label === result.band.label)?.p ?? 0, 2)}`}
          />
          <KpiTile
            label="Cluster"
            value={<span className="text-base">{result.cluster.cluster === 0 ? "Critical risk" : "Low risk"}</span>}
            hint={`profile group · distance ${num(result.cluster.distance, 2)}`}
          />
        </div>

        <Card title="Risk-band probabilities" subtitle="Multinomial logistic regression output">
          <div className="space-y-2.5">
            {result.band.probabilities
              .slice()
              .sort((a, b) => b.p - a.p)
              .map((b) => (
                <div key={b.label} className="flex items-center gap-3">
                  <div className="w-20 shrink-0">
                    <RiskBandBadge band={b.label} />
                  </div>
                  <div className="flex-1 overflow-hidden rounded-full bg-zinc-100">
                    <div
                      className={cn(
                        "h-2 rounded-full transition-all duration-300",
                        b.label === result.band.label
                          ? "bg-gradient-to-r from-red-500 to-red-700"
                          : "bg-zinc-300",
                      )}
                      style={{ width: `${Math.max(2, b.p * 100)}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-sm font-medium tabular-nums text-zinc-700">
                    {(b.p * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
          </div>
        </Card>

        <Card title="Most similar real sub-populations" subtitle="Nearest neighbours among the 220 DHS observations">
          <ul className="divide-y divide-zinc-100">
            {similar.map(({ row, distance }, i) => {
              const dim = row.breakdown_dim ?? "Region";
              const isRegion = dim === "Region";
              return (
                <li
                  key={`${dim}|${row.subregion}|${row.year}|${i}`}
                  className="flex items-center justify-between gap-3 py-2.5 text-sm"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-zinc-900 truncate">
                        {row.subregion}
                      </span>
                      <span className="rounded-full bg-zinc-100 px-1.5 py-0.5 text-[10px] font-medium text-zinc-600 shrink-0">
                        {isRegion ? "region" : dim.toLowerCase()}
                      </span>
                    </div>
                    <div className="text-xs text-zinc-500">{row.year} DHS round</div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-sm font-medium text-zinc-900 tabular-nums">
                      {pct(row.stunting_rate, 1)}
                    </span>
                    <span className="rounded-full bg-zinc-50 px-1.5 py-0.5 text-[10px] text-zinc-500 tabular-nums">
                      d {num(distance, 2)}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        </Card>
      </div>
    </div>
  );
}
