import { Card } from "@/components/Card";
import { KpiTile } from "@/components/KpiTile";
import { getHypotheses, getSummary } from "@/lib/data";
import { num, pval } from "@/lib/format";
import { CheckCircle2, XCircle } from "lucide-react";

export const metadata = { title: "Hypotheses — Cameroon Malnutrition Atlas" };

const STATEMENTS: Record<string, { stmt: string; sign: string; method: string }> = {
  H1: { stmt: "Maternal education (% women with secondary+ schooling) is negatively associated with stunting.",
         sign: "negative", method: "Spearman ρ on women_secondary_plus_pct" },
  H2: { stmt: "Improved water + sanitation are negatively associated with stunting.",
         sign: "negative", method: "Spearman ρ on WASH composite (mean of water + sanitation)" },
  H3: { stmt: "Socio-economic status (proxy: women literate + secondary+) is negatively associated with stunting.",
         sign: "negative", method: "Spearman ρ on a literacy/secondary-edu composite (the HDX subnational extract does not include DHS wealth quintiles for Cameroon, so we use the documented education proxy)" },
  H4: { stmt: "Healthcare access (proxy: health-facility delivery share) is negatively associated with stunting.",
         sign: "negative", method: "Spearman ρ on health_facility_delivery_pct (DHS does not publish per-region facility counts; this is the standard access proxy)" },
  H5: { stmt: "Malaria prevalence is positively associated with stunting.",
         sign: "positive", method: "Spearman ρ on malaria_prevalence_pct (RDT)" },
  H6: { stmt: "The ML regression model beats the mean-baseline on cross-validated RMSE.",
         sign: "lower",    method: "One-sided paired t-test on per-fold RMSE differences" },
};

export default async function HypothesesPage() {
  const [rows, summary] = await Promise.all([getHypotheses(), getSummary()]);

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Hypothesis tests</h1>
        <p className="mt-1 text-zinc-600">
          Six hypotheses from the project proposal. Tests at significance level &alpha; = 0.05.
          We reject the null when the p-value is below 0.05 <em>and</em> the sign of the
          effect matches the alternative hypothesis&apos;s prediction.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Supported"   value={`${summary.n_hypotheses_supported} / ${summary.n_hypotheses_total}`} tone="good" />
        <KpiTile label="Significance" value="α = 0.05" />
        <KpiTile label="Sample size" value={rows[0]?.n ?? "—"} hint="sub-region × year rows" />
        <KpiTile label="H6 method"   value="paired t-test" hint="per-fold RMSE differences" />
      </div>

      <div className="grid gap-4">
        {rows.map((r) => {
          const meta = STATEMENTS[r.hypothesis] ?? { stmt: r.hypothesis, sign: "?", method: "?" };
          return (
            <Card
              key={r.hypothesis}
              title={
                <div className="flex items-center gap-3">
                  <span>{r.hypothesis}</span>
                  {r.reject_null ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Supported
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600">
                      <XCircle className="h-3.5 w-3.5" /> Not supported
                    </span>
                  )}
                </div>
              }
              subtitle={meta.stmt}
            >
              <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-[160px_1fr]">
                <dt className="text-zinc-500">Predicted direction</dt>
                <dd className="font-medium text-zinc-800">{meta.sign}</dd>
                <dt className="text-zinc-500">Method</dt>
                <dd className="text-zinc-800">{meta.method}</dd>
                {r.feature && (
                  <>
                    <dt className="text-zinc-500">Feature</dt>
                    <dd className="font-mono text-xs text-zinc-700">{r.feature}</dd>
                  </>
                )}
                {r.rho != null && (
                  <>
                    <dt className="text-zinc-500">Spearman rho</dt>
                    <dd className="tabular-nums text-zinc-800">{num(r.rho, 3)}</dd>
                  </>
                )}
                <dt className="text-zinc-500">p-value</dt>
                <dd className="tabular-nums text-zinc-800">{pval(r.p_value)}</dd>
                {r.ml_rmse_mean != null && (
                  <>
                    <dt className="text-zinc-500">ML CV RMSE</dt>
                    <dd className="tabular-nums text-zinc-800">{num(r.ml_rmse_mean, 3)}</dd>
                    <dt className="text-zinc-500">Baseline CV RMSE</dt>
                    <dd className="tabular-nums text-zinc-800">{num(r.baseline_rmse_mean ?? 0, 3)}</dd>
                    <dt className="text-zinc-500">Improvement</dt>
                    <dd className="text-emerald-700 font-medium">{num(r.improvement_pct ?? 0, 1)}%</dd>
                  </>
                )}
              </dl>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
