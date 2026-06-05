import Link from "next/link";
import {
  ArrowRight, LineChart, MapPinned, ScatterChart, TrendingUp,
  Database, Activity, Award,
} from "lucide-react";
import ChoroplethMap from "@/components/ChoroplethMap";
import { Card } from "@/components/Card";
import { KpiTile } from "@/components/KpiTile";
import { DataTable } from "@/components/DataTable";
import { RiskBandBadge } from "@/components/Badge";
import { HypothesisStrip } from "@/components/HypothesisStrip";
import { DataBanner } from "@/components/DataBanner";
import {
  getHotspots, getHypotheses, getRegionAgg, getSummary,
} from "@/lib/data";
import { num, pct } from "@/lib/format";

export default async function HomePage() {
  const [summary, regions, hotspots, hypotheses] = await Promise.all([
    getSummary(), getRegionAgg(), getHotspots(), getHypotheses(),
  ]);

  const regionValues: Record<string, number> = Object.fromEntries(
    regions.map((r) => [r.region, r.predicted_stunting_mean])
  );
  const top10 = hotspots.slice(0, 10);

  return (
    <div className="flex flex-col gap-10">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-zinc-200/80 hero-bg p-8 sm:p-10">
        <div className="absolute -top-20 -right-20 h-72 w-72 rounded-full bg-red-200/30 blur-3xl" />
        <div className="absolute -bottom-32 -left-16 h-80 w-80 rounded-full bg-amber-200/40 blur-3xl" />
        <div className="relative grid gap-10 lg:grid-cols-[1.1fr_1fr] lg:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-red-200 bg-white/80 px-3 py-1 text-xs font-medium text-red-700 shadow-sm backdrop-blur">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-red-600 animate-pulse" />
              CEC 420 · Data Mining · University of Buea
            </div>
            <h1 className="mt-4 text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-zinc-900 leading-[1.05]">
              Where are Cameroon&apos;s child-malnutrition{" "}
              <span className="bg-gradient-to-r from-red-600 to-orange-500 bg-clip-text text-transparent">
                hotspots
              </span>?
            </h1>
            <p className="mt-4 max-w-xl text-base text-zinc-700 leading-relaxed">
              {pct(summary.national_mean_stunting, 0)} of children under five were
              stunted at the {summary.latest_year} DHS round, with the burden
              concentrated in the north. This atlas applies four data-mining
              techniques — regression, classification, clustering and forecasting —
              to {summary.n_subregions} real DHS sub-populations across {" "}
              {summary.survey_years[0]}–{summary.latest_year}.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/hotspots"
                className="group inline-flex items-center gap-2 rounded-lg bg-red-600 px-5 py-2.5 text-sm font-medium text-white shadow-md shadow-red-600/20 transition-all hover:bg-red-700 hover:shadow-lg hover:shadow-red-600/30"
              >
                <MapPinned className="h-4 w-4" />
                See the hotspot ranking
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          </div>
          <div className="relative rounded-2xl bg-white/85 p-3 ring-1 ring-zinc-200 shadow-xl backdrop-blur">
            <ChoroplethMap values={regionValues} height={380} />
          </div>
        </div>
      </section>

      <DataBanner />

      {/* KPIs */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile
          icon={<Activity className="h-3.5 w-3.5" />}
          label={`Mean stunting · ${summary.latest_year}`}
          value={pct(summary.national_mean_stunting, 1)}
          hint={`across ${summary.n_regions} Cameroon admin-1 regions`}
          tone="danger"
        />
        <KpiTile
          icon={<MapPinned className="h-3.5 w-3.5" />}
          label="Worst region"
          value={pct(summary.worst_subregion_pct, 1)}
          hint="single region with highest measured stunting"
          tone="danger"
        />
        <KpiTile
          icon={<Award className="h-3.5 w-3.5" />}
          label="Best model"
          value={<span className="text-2xl">{summary.best_model}</span>}
          hint={`CV-RMSE ${num(summary.best_cv_rmse, 2)} vs ${num(summary.baseline_cv_rmse, 2)} baseline`}
          tone="good"
        />
        <KpiTile
          icon={<Database className="h-3.5 w-3.5" />}
          label="Hypotheses supported"
          value={`${summary.n_hypotheses_supported} / ${summary.n_hypotheses_total}`}
          hint={`H1–H6 at α = 0.05 on real DHS data`}
          tone="good"
        />
      </section>

      {/* H1-H6 strip */}
      <section>
        <div className="mb-3 flex items-baseline justify-between">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-zinc-900">
              Hypotheses H1 – H6
            </h2>
            <p className="text-sm text-zinc-500">Tested on real DHS regional series at α = 0.05</p>
          </div>
          <Link href="/hypotheses" className="text-sm font-medium text-red-700 hover:text-red-800">
            See details →
          </Link>
        </div>
        <HypothesisStrip rows={hypotheses} />
      </section>

      {/* Top 10 + technique grid */}
      <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card
          title={`Top ${top10.length} predicted hotspots`}
          subtitle={`${summary.best_model} prediction · ${summary.latest_year} DHS round`}
          right={
            <Link
              href="/hotspots"
              className="text-sm font-medium text-red-700 hover:text-red-800"
            >
              View all →
            </Link>
          }
        >
          <DataTable
            rows={top10}
            cols={[
              { key: "rank", label: "#", align: "right", className: "w-10 text-zinc-400" },
              { key: "region", label: "Region" },
              {
                key: "predicted_stunting", label: "Predicted", align: "right",
                render: (r) => <span className="font-semibold tabular-nums">{pct(r.predicted_stunting, 1)}</span>,
              },
              {
                key: "predicted_band", label: "Band", align: "center",
                render: (r) => <RiskBandBadge band={r.predicted_band} />,
              },
              {
                key: "forecast_2028", label: "→ 2028", align: "right",
                render: (r) => r.forecast_2028 != null ? <span className="text-zinc-500">{pct(r.forecast_2028, 1)}</span> : "—",
              },
            ]}
          />
        </Card>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-1">
          {[
            { icon: ScatterChart, href: "/regression",     title: "Regression",     body: "9 models, 5-fold CV RMSE.",   tone: "from-zinc-50 to-white border-zinc-200/60 text-zinc-700" },
            { icon: MapPinned,    href: "/classification", title: "Classification", body: "WHO 4-band risk classifier.", tone: "from-zinc-50 to-white border-zinc-200/60 text-zinc-700" },
            { icon: LineChart,    href: "/clustering",     title: "Clustering",     body: "K-Means on driver profiles.", tone: "from-zinc-50 to-white border-zinc-200/60 text-zinc-700" },
            { icon: TrendingUp,   href: "/forecasts",      title: "Forecasts",      body: "Trends to 2026 / 2028.",      tone: "from-zinc-50 to-white border-zinc-200/60 text-zinc-700" },
          ].map(({ icon: Icon, href, title, body, tone }) => (
            <Link
              key={href}
              href={href}
              className={`group block rounded-xl border bg-gradient-to-br p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md ${tone}`}
            >
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-white/80 p-2 ring-1 ring-zinc-200/60">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-zinc-900">
                    {title}
                  </h3>
                  <p className="text-xs text-zinc-600">{body}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-zinc-400 transition-transform group-hover:translate-x-0.5 group-hover:text-zinc-900" />
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
