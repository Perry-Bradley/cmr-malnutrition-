import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { RiskBandBadge } from "@/components/Badge";
import { DataBanner } from "@/components/DataBanner";
import { getHotspots, getSummary } from "@/lib/data";
import { num, pct } from "@/lib/format";

export const metadata = { title: "Hotspots — Cameroon Malnutrition Atlas" };

export default async function HotspotsPage() {
  const [summary, hotspots] = await Promise.all([
    getSummary(), getHotspots(),
  ]);

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Predicted child-malnutrition hotspots
        </h1>
        <p className="mt-1 text-zinc-600">
          Every Cameroon admin-1 region in {summary.latest_year}, ranked by predicted stunting rate.
        </p>
      </header>

      <DataBanner />

      <Card
        title="Full regional ranking"
        subtitle="Predicted stunting + WHO risk band + cluster + forecast"
      >
        <DataTable
          rows={hotspots}
          cols={[
            { key: "rank", label: "#", align: "right", className: "w-10" },
            { key: "region", label: "Region", className: "font-medium text-zinc-900" },
            {
              key: "predicted_stunting", label: "Predicted", align: "right",
              render: (r) => <span className="font-semibold text-zinc-900 tabular-nums">{pct(r.predicted_stunting, 1)}</span>,
            },
            {
              key: "predicted_band", label: "WHO Risk Band", align: "center",
              render: (r) => <RiskBandBadge band={r.predicted_band} />,
            },
            {
              key: "cluster_label", label: "Cluster", className: "text-zinc-500",
              render: (r) => r.cluster_label ?? "—",
            },
            {
              key: "forecast_2026", label: "→ 2026", align: "right",
              render: (r) => (r.forecast_2026 != null ? <span className="text-zinc-500 tabular-nums">{num(r.forecast_2026, 1)}%</span> : "—"),
            },
            {
              key: "forecast_2028", label: "→ 2028", align: "right",
              render: (r) => (r.forecast_2028 != null ? <span className="text-zinc-500 tabular-nums">{num(r.forecast_2028, 1)}%</span> : "—"),
            },
          ]}
        />
      </Card>
    </div>
  );
}

