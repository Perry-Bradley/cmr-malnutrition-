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
          Stunting rate is binned into four WHO risk bands and a multi-class classifier is trained on the same features.
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

    </div>
  );
}
