import Link from "next/link";
import { notFound } from "next/navigation";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { KpiTile } from "@/components/KpiTile";
import { RiskBandBadge } from "@/components/Badge";
import {
  getClusterAssignments, getForecasts, getHotspots, getSubregional, getTrends,
} from "@/lib/data";
import { num, pct, REGION_COLOR } from "@/lib/format";

type Props = { params: Promise<{ name: string }> };

export async function generateStaticParams() {
  const rows = await getSubregional();
  return Array.from(new Set(rows.map((r) => r.region))).map((name) => ({
    name: encodeURIComponent(name),
  }));
}

const FEATURE_LABEL: Record<string, string> = {
  women_secondary_plus_pct:     "Women with secondary+ education",
  women_literate_pct:           "Women literate",
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
  fertility_rate:               "Total fertility rate",
};

export default async function RegionPage({ params }: Props) {
  const { name } = await params;
  const region = decodeURIComponent(name);

  const [rows, hotspots, trends, forecasts, clusters] = await Promise.all([
    getSubregional(), getHotspots(), getTrends(), getForecasts(),
    getClusterAssignments(),
  ]);

  const history = rows.filter((r) => r.region === region)
                       .sort((a, b) => a.year - b.year);
  if (!history.length) notFound();

  const latest = history[history.length - 1];
  const hotspot = hotspots.find((h) => h.region === region);
  const trend = trends.find((t) => t.region === region);
  const fcs = forecasts.filter((f) => f.region === region);
  const cluster = clusters.find((c) => c.region === region);

  const slope = trend?.slope_pp_per_year ?? 0;
  const color = REGION_COLOR[region] ?? "#475569";

  return (
    <div className="flex flex-col gap-8">
      <header>
        <Link href="/hotspots" className="text-sm text-zinc-500 hover:text-zinc-900">
          ← All regions
        </Link>
        <div className="mt-2 flex items-center gap-3">
          <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            {region}
          </h1>
          <span className="text-zinc-500">— stunting profile across DHS rounds</span>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label={`Stunting (${latest.year})`}    value={pct(latest.stunting_rate, 1)} tone={latest.stunting_rate >= 30 ? "danger" : latest.stunting_rate >= 20 ? "warning" : "good"} />
        <KpiTile label="Predicted (model)"               value={hotspot ? pct(hotspot.predicted_stunting, 1) : "—"} hint="Gradient Boosting" />
        <KpiTile label="Predicted band"                  value={<RiskBandBadge band={hotspot?.predicted_band} />} />
        <KpiTile
          label="Trend"
          value={`${slope >= 0 ? "+" : ""}${num(slope, 2)} pp/yr`}
          hint={slope < 0 ? "improving" : "stagnant/worsening"}
          tone={slope < 0 ? "good" : "warning"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <Card title="Historical + forecast" subtitle={`Observed ${history[0].year} - ${latest.year} + linear extrapolation to 2026 / 2028`}>
          <DataTable
            rows={[
              ...history.map((h) => ({ year: h.year, value: h.stunting_rate, kind: "observed" as const })),
              ...fcs.map((f)   => ({ year: f.year, value: f.forecast_stunting, kind: "forecast" as const })),
            ].sort((a, b) => a.year - b.year)}
            cols={[
              { key: "year",  label: "Year",         align: "right" },
              { key: "value", label: "Stunting (%)", align: "right", render: (r) => pct(r.value as number, 1) },
              { key: "kind",  label: "Type", render: (r) => (
                  <span className={r.kind === "forecast" ? "text-amber-700" : "text-zinc-700"}>
                    {r.kind as string}
                  </span>
                ) },
            ]}
          />
        </Card>

        <Card title="Cluster + similar regions" subtitle="Assigned by K-Means on the driver profile">
          <div className="space-y-3">
            <div>
              <div className="text-xs uppercase tracking-wide text-zinc-500">Cluster</div>
              <div className="text-base font-medium text-zinc-900">
                {cluster?.cluster_label ?? "—"}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-zinc-500">Cluster size</div>
              <div className="text-base font-medium text-zinc-900">
                {clusters.filter((c) => c.cluster_label === cluster?.cluster_label).length} regions
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-zinc-500">Forecast 2028</div>
              <div className="text-base font-medium text-zinc-900">
                {hotspot?.forecast_2028 != null ? pct(hotspot.forecast_2028, 1) : "—"}
              </div>
            </div>
            <div className="pt-2">
              <Link
                href="/predict"
                className="inline-flex items-center gap-1.5 rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-zinc-800"
              >
                Try the what-if predictor →
              </Link>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Current driver profile" subtitle={`Real DHS values for ${region}, ${latest.year}`}>
        <DataTable
          rows={Object.entries(FEATURE_LABEL).map(([key, label]) => ({
            label,
            value: (latest as unknown as Record<string, number>)[key],
            key,
          }))}
          cols={[
            { key: "label", label: "Feature" },
            { key: "value", label: "Value", align: "right",
              render: (r) => (typeof r.value === "number"
                ? (r.key === "fertility_rate" ? num(r.value, 2) : pct(r.value as number, 1))
                : "—") },
          ]}
        />
      </Card>
    </div>
  );
}
