import { Card } from "@/components/Card";
import { KpiTile } from "@/components/KpiTile";
import { getHypotheses, getSummary } from "@/lib/data";
import { num, pval } from "@/lib/format";
import { CheckCircle2, XCircle } from "lucide-react";

export const metadata = { title: "Hypotheses — Cameroon Malnutrition Atlas" };

const STATEMENTS: Record<string, { stmt: string; sign: string }> = {
  H1: { stmt: "Maternal education is negatively associated with stunting.",           sign: "negative" },
  H2: { stmt: "Improved water and sanitation access is negatively associated with stunting.", sign: "negative" },
  H3: { stmt: "Socio-economic status is negatively associated with stunting.",        sign: "negative" },
  H4: { stmt: "Healthcare facility access is negatively associated with stunting.",   sign: "negative" },
  H5: { stmt: "Malaria prevalence is positively associated with stunting.",           sign: "positive" },
  H6: { stmt: "The ML model beats the naive mean-baseline on cross-validated RMSE.",  sign: "lower"    },
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
                {r.rho != null && (
                  <>
                    <dt className="text-zinc-500">Spearman ρ</dt>
                    <dd className="tabular-nums text-zinc-800">{num(r.rho, 3)}</dd>
                  </>
                )}
                <dt className="text-zinc-500">p-value</dt>
                <dd className="tabular-nums text-zinc-800">{pval(r.p_value)}</dd>
                {r.improvement_pct != null && (
                  <>
                    <dt className="text-zinc-500">Improvement over baseline</dt>
                    <dd className="text-emerald-700 font-medium">{num(r.improvement_pct, 1)}%</dd>
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
