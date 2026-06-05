import { Card } from "@/components/Card";
import { ConfusionMatrix } from "@/components/ConfusionMatrix";
import { DataTable } from "@/components/DataTable";
import { KpiTile } from "@/components/KpiTile";
import { RiskBandBadge } from "@/components/Badge";
import {
  getClassifierLB, getClassifierReports, getHotspots,
} from "@/lib/data";
import { num } from "@/lib/format";

export const metadata = { title: "Classification — Cameroon Malnutrition Atlas" };

const BAND_DESCRIPTIONS: Record<string, string> = {
  low:      "<20% stunting — public-health significance is low.",
  medium:   "20-29% stunting — medium significance, monitoring warranted.",
  high:     "30-39% stunting — high significance, intervention recommended.",
  critical: "≥40% stunting — very high significance, emergency response.",
};

export default async function ClassificationPage() {
  const [lb, reports, hotspots] = await Promise.all([
    getClassifierLB(), getClassifierReports(), getHotspots(),
  ]);
  const sorted = [...lb].sort((a, b) => b.cv_accuracy_mean - a.cv_accuracy_mean);
  const best = sorted[0];
  const bestReport = reports[best.name];

  // band distribution across all hotspot sub-regions
  const bandCounts: Record<string, number> = {};
  hotspots.forEach((h) => {
    if (!h.predicted_band) return;
    bandCounts[h.predicted_band] = (bandCounts[h.predicted_band] ?? 0) + 1;
  });

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Classification</h1>
        <p className="mt-1 text-zinc-600">
          Same features, different framing: bin the stunting rate into the four WHO
          public-health categories and train a classifier. Useful when programmes need
          a categorical decision (e.g. trigger an emergency response only on
          &ldquo;critical&rdquo;).
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Best classifier" value={best.name}                                      tone="good" />
        <KpiTile label="CV accuracy"     value={`${(best.cv_accuracy_mean * 100).toFixed(1)}%`}  hint={`+/- ${(best.cv_accuracy_std * 100).toFixed(1)} pp`} tone="good" />
        <KpiTile label="Macro F1"        value={num(best.macro_f1, 3)}                          hint="balanced across classes" />
        <KpiTile label="Test accuracy"   value={`${(best.accuracy * 100).toFixed(1)}%`}          hint="20% hold-out" />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <Card title={`Confusion matrix — ${best.name}`} subtitle="rows = actual, columns = predicted">
          <ConfusionMatrix matrix={bestReport.confusion_matrix} labels={bestReport.labels} />
        </Card>

        <Card
          title="WHO risk bands"
          subtitle="Public-health classification of stunting prevalence"
        >
          <ul className="space-y-2">
            {bestReport.labels.map((b) => (
              <li key={b} className="flex items-center gap-3">
                <RiskBandBadge band={b} />
                <span className="text-sm text-zinc-600">{BAND_DESCRIPTIONS[b]}</span>
                <span className="ml-auto text-sm font-medium text-zinc-700">
                  {bandCounts[b] ?? 0} sub-regions
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card title="Per-class metrics (best model)">
        <DataTable
          rows={bestReport.labels.map((label) => {
            const r = bestReport.classification_report[label] as Record<string, number>;
            return {
              label,
              precision: r?.precision ?? 0,
              recall: r?.recall ?? 0,
              f1: r?.["f1-score"] ?? 0,
              support: r?.support ?? 0,
            };
          })}
          cols={[
            { key: "label",     label: "Band", render: (r) => <RiskBandBadge band={r.label as string} /> },
            { key: "precision", label: "Precision", align: "right", render: (r) => num(r.precision as number, 3) },
            { key: "recall",    label: "Recall",    align: "right", render: (r) => num(r.recall as number, 3) },
            { key: "f1",        label: "F1",        align: "right", render: (r) => num(r.f1 as number, 3) },
            { key: "support",   label: "Support",   align: "right" },
          ]}
        />
      </Card>

      <Card title="Classifier leaderboard">
        <DataTable
          rows={sorted}
          cols={[
            { key: "name", label: "Model" },
            { key: "accuracy",         label: "Test accuracy", align: "right", render: (r) => `${((r.accuracy as number) * 100).toFixed(1)}%` },
            { key: "macro_f1",         label: "Macro F1",      align: "right", render: (r) => num(r.macro_f1 as number, 3) },
            { key: "cv_accuracy_mean", label: "CV accuracy",   align: "right", render: (r) => `${((r.cv_accuracy_mean as number) * 100).toFixed(1)}%` },
            { key: "cv_accuracy_std",  label: "CV std",        align: "right", render: (r) => `${((r.cv_accuracy_std as number) * 100).toFixed(2)} pp` },
          ]}
        />
      </Card>
    </div>
  );
}
