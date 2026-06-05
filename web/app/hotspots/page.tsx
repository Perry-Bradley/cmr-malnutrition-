import Link from "next/link";
import ChoroplethMap from "@/components/ChoroplethMap";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { RiskBandBadge } from "@/components/Badge";
import { DataBanner } from "@/components/DataBanner";
import { getHotspots, getRegionAgg, getSummary } from "@/lib/data";
import { num, pct } from "@/lib/format";

export const metadata = { title: "Hotspots — Cameroon Malnutrition Atlas" };

export default async function HotspotsPage() {
  const [summary, regions, hotspots] = await Promise.all([
    getSummary(), getRegionAgg(), getHotspots(),
  ]);

  const regionValues: Record<string, number> = Object.fromEntries(
    regions.map((r) => [r.region, r.predicted_stunting_mean])
  );

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Predicted child-malnutrition hotspots
        </h1>
        <p className="mt-1 text-zinc-600">
          Every Cameroon admin-1 region in {summary.latest_year}, ranked by the
          {" "}{summary.best_model} prediction. Click a region to drill in.
        </p>
      </header>

      <DataBanner />

      <div className="grid gap-6 lg:grid-cols-[1.05fr_1fr]">
        <Card title="Regional choropleth" subtitle="Predicted stunting rate per region">
          <ChoroplethMap values={regionValues} height={440} />
        </Card>

        <Card
          title="Full ranking"
          subtitle="Predicted stunting + WHO risk band + cluster + forecast"
        >
          <DataTable
            rows={hotspots}
            cols={[
              { key: "rank", label: "#", align: "right", className: "w-10" },
              {
                key: "region", label: "Region",
                render: (r) => (
                  <Link
                    href={`/region/${encodeURIComponent(r.region)}`}
                    className="font-medium text-zinc-900 hover:underline"
                  >
                    {r.region}
                  </Link>
                ),
              },
              {
                key: "predicted_stunting", label: "Predicted", align: "right",
                render: (r) => <span className="font-medium">{pct(r.predicted_stunting, 1)}</span>,
              },
              {
                key: "predicted_band", label: "Band", align: "center",
                render: (r) => <RiskBandBadge band={r.predicted_band} />,
              },
              {
                key: "cluster_label", label: "Cluster", className: "text-zinc-500",
                render: (r) => r.cluster_label ?? "—",
              },
              {
                key: "forecast_2026", label: "→ 2026", align: "right",
                render: (r) => (r.forecast_2026 != null ? num(r.forecast_2026, 1) : "—"),
              },
              {
                key: "forecast_2028", label: "→ 2028", align: "right",
                render: (r) => (r.forecast_2028 != null ? num(r.forecast_2028, 1) : "—"),
              },
            ]}
          />
        </Card>
      </div>
    </div>
  );
}
