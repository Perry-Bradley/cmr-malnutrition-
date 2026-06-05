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

  // join trend + forecasts into one row per sub-region
  const forecastsBySub: Record<string, { f2026?: number; f2028?: number }> = {};
  for (const f of forecasts) {
    const k = `${f.region}|${f.subregion}`;
    forecastsBySub[k] = forecastsBySub[k] ?? {};
    if (f.year === 2026) forecastsBySub[k].f2026 = f.forecast_stunting;
    if (f.year === 2028) forecastsBySub[k].f2028 = f.forecast_stunting;
  }
  const merged = trends.map((t) => ({
    ...t,
    forecast_2026: forecastsBySub[`${t.region}|${t.subregion}`]?.f2026,
    forecast_2028: forecastsBySub[`${t.region}|${t.subregion}`]?.f2028,
  }));

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Forecasts</h1>
        <p className="mt-1 text-zinc-600">
          A linear trend is fitted to each sub-region&apos;s observed stunting series and
          extrapolated to 2026 and 2028. Slope (in percentage points per year) is the
          most informative single number — negative means improving, positive means
          stagnating or worsening.
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

      <Card title="All sub-regions: trend + forecast"
            subtitle="Sorted by predicted 2028 stunting rate (highest risk first)">
        <DataTable
          rows={[...merged].sort((a, b) => (b.forecast_2028 ?? 0) - (a.forecast_2028 ?? 0))}
          cols={[
            { key: "subregion",       label: "Sub-region" },
            { key: "region",          label: "Region", className: "text-zinc-500" },
            { key: "last_observed",   label: `Last obs (${trends[0]?.last_year ?? ""})`, align: "right",
              render: (r) => pct(r.last_observed, 1) },
            { key: "slope_pp_per_year", label: "Slope (pp/yr)", align: "right",
              render: (r) => (
                <span className={r.slope_pp_per_year < 0 ? "text-emerald-700" : "text-red-700"}>
                  {num(r.slope_pp_per_year, 2)}
                </span>
              ) },
            { key: "r2",              label: "Trend R²", align: "right", render: (r) => num(r.r2, 2) },
            { key: "forecast_2026",   label: "2026", align: "right", render: (r) => r.forecast_2026 != null ? pct(r.forecast_2026, 1) : "—" },
            { key: "forecast_2028",   label: "2028", align: "right", render: (r) => r.forecast_2028 != null ? pct(r.forecast_2028, 1) : "—" },
          ]}
        />
      </Card>
    </div>
  );
}
