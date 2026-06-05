import Link from "next/link";
import { CheckCircle2, XCircle, TrendingDown, TrendingUp } from "lucide-react";
import type { HypothesisRow } from "@/lib/types";
import { cn, num, pval } from "@/lib/format";

const H_TITLE: Record<string, string> = {
  H1: "Maternal education ↓ stunting",
  H2: "WASH access ↓ stunting",
  H3: "Socio-economic status ↓ stunting",
  H4: "Healthcare access ↓ stunting",
  H5: "Malaria prevalence ↑ stunting",
  H6: "ML beats baseline",
};

export function HypothesisStrip({ rows }: { rows: HypothesisRow[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {rows.map((r) => {
        const ok = r.reject_null;
        const isPositive = (r.rho ?? 0) > 0;
        const TrendIcon = isPositive ? TrendingUp : TrendingDown;
        return (
          <Link
            key={r.hypothesis}
            href="/hypotheses"
            className={cn(
              "group relative block overflow-hidden rounded-2xl border bg-white p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md",
              ok ? "border-emerald-200/70" : "border-zinc-200",
            )}
          >
            {ok && (
              <div className="absolute right-0 top-0 h-16 w-16 bg-gradient-to-bl from-emerald-100/60 to-transparent" />
            )}
            <div className="relative flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold tracking-wider text-zinc-500">
                    {r.hypothesis}
                  </span>
                  {ok ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100/80 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700">
                      <CheckCircle2 className="h-3 w-3" /> Supported
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                      <XCircle className="h-3 w-3" /> Not supported
                    </span>
                  )}
                </div>
                <h3 className="mt-1.5 text-sm font-semibold leading-tight text-zinc-900">
                  {H_TITLE[r.hypothesis] ?? r.hypothesis}
                </h3>
              </div>
              {r.rho != null && (
                <div className={cn(
                  "shrink-0 rounded-lg p-1.5",
                  isPositive ? "bg-red-50 text-red-600" : "bg-emerald-50 text-emerald-600"
                )}>
                  <TrendIcon className="h-3.5 w-3.5" />
                </div>
              )}
            </div>
            <dl className="relative mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs text-zinc-600">
              {r.rho != null && (
                <>
                  <dt>Spearman ρ</dt>
                  <dd className="text-right tabular-nums font-semibold text-zinc-900">
                    {num(r.rho, 3)}
                  </dd>
                </>
              )}
              {r.improvement_pct != null && (
                <>
                  <dt>RMSE drop</dt>
                  <dd className="text-right tabular-nums font-semibold text-emerald-700">
                    {num(r.improvement_pct, 1)}%
                  </dd>
                </>
              )}
              <dt>p-value</dt>
              <dd className="text-right tabular-nums text-zinc-700">{pval(r.p_value)}</dd>
            </dl>
          </Link>
        );
      })}
    </div>
  );
}
