import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { KpiTile } from "@/components/KpiTile";
import { getForecasts, getTrends } from "@/lib/data";
import { num, pct } from "@/lib/format";

export const metadata = { title: "Forecasts — Cameroon Malnutrition Atlas" };

export default async function ForecastsPage() {
  const [trends, forecasts] = await Promise.all([getTrends(), getForecasts()]);

  const meanSlope = trends.reduce((s, t) => s + t.slope_pp_per_year, 0) / Math.max(1, trends.length);
  const fastestImproving = [...trends].sort((a, b) => a.slope_pp_per_year - b.slope_pp_per_year).slice(0, 5);
  const stagnant = [...trends].sort((a, b) => b.slope_pp_per_year - a.slope_pp_per_year).slice(0, 5);

  const fc2026 = forecasts.filter((f) => f.year === 2026);
  const fc2028 = forecasts.filter((f) => f.year === 2028);
  const mean2026 = fc2026.reduce((s, f) => s + f.forecast_stunting, 0) / Math.max(1, fc2026.length);
  const mean2028 = fc2028.reduce((s, f) => s + f.forecast_stunting, 0) / Math.max(1, fc2028.length);

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Forecasts</h1>
        <p className="mt-1 text-zinc-600">
          Linear trends fitted per sub-region, extrapolated to 2026 and 2028. Negative slope = improving.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Mean slope" value={`${num(meanSlope, 2)} pp/yr`} hint="negative = improving"
                 tone={meanSlope < 0 ? "good" : "warning"} />
        <KpiTile label="Forecast 2026 mean" value={pct(mean2026, 1)} tone="warning" />
        <KpiTile label="Forecast 2028 mean" value={pct(mean2028, 1)} tone="warning" />
        <KpiTile label="Sub-regions forecast" value={trends.length} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Fastest-improving sub-regions" subtitle="Most-negative slope">
          <DataTable
            rows={fastestImproving}
            cols={[
              { key: "subregion", label: "Sub-region" },
              { key: "region", label: "Region", className: "text-zinc-500" },
              { key: "slope_pp_per_year", label: "Slope (pp/yr)", align: "right",
                render: (r) => <span className="text-emerald-700">{num(r.slope_pp_per_year, 2)}</span> },
              { key: "last_observed", label: "Last obs.", align: "right", render: (r) => pct(r.last_observed, 1) },
            ]}
          />
        </Card>

        <Card title="Slowest-improving sub-regions" subtitle="Most-positive (or least-negative) slope">
          <DataTable
            rows={stagnant}
            cols={[
              { key: "subregion", label: "Sub-region" },
              { key: "region", label: "Region", className: "text-zinc-500" },
              { key: "slope_pp_per_year", label: "Slope (pp/yr)", align: "right",
                render: (r) => <span className="text-red-700">{num(r.slope_pp_per_year, 2)}</span> },
              { key: "last_observed", label: "Last obs.", align: "right", render: (r) => pct(r.last_observed, 1) },
            ]}
          />
        </Card>
      </div>

    </div>
  );
}
