import BarChart from "@/components/BarChart";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { KpiTile } from "@/components/KpiTile";
import { getLeaderboard, getSummary } from "@/lib/data";
import { num } from "@/lib/format";

export const metadata = { title: "Regression — Cameroon Malnutrition Atlas" };

export default async function RegressionPage() {
  const [leaderboard, summary] = await Promise.all([getLeaderboard(), getSummary()]);
  const sorted = [...leaderboard].sort((a, b) => a.cv_rmse_mean - b.cv_rmse_mean);
  const best = sorted[0];
  const baseline = sorted.find((r) => r.name.toLowerCase().includes("baseline")) ?? sorted[sorted.length - 1];
  const improvement = ((baseline.cv_rmse_mean - best.cv_rmse_mean) / baseline.cv_rmse_mean) * 100;

  const chartData = [...sorted].reverse().map((r) => ({
    name: r.name,
    cv_rmse: Number(r.cv_rmse_mean.toFixed(3)),
    cv_std:  Number(r.cv_rmse_std.toFixed(3)),
  }));

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Regression</h1>
        <p className="mt-1 text-zinc-600">
          Models are compared on 5-fold cross-validated RMSE. The best model is used to rank hotspots.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Best model"     value={best.name}                       tone="good" />
        <KpiTile label="Best CV RMSE"   value={num(best.cv_rmse_mean, 2)}        hint={`+/- ${num(best.cv_rmse_std, 2)}`} tone="good" />
        <KpiTile label="Baseline RMSE"  value={num(baseline.cv_rmse_mean, 2)}    hint="predict national mean" />
        <KpiTile label="Improvement"    value={`${improvement.toFixed(1)}%`}     hint="vs baseline" tone="good" />
      </div>

      <Card
        title="Model leaderboard"
        subtitle="Lower CV RMSE is better. Error bars = standard deviation across folds."
      >
        <BarChart
          data={chartData}
          xKey="name"
          yKey="cv_rmse"
          errorKey="cv_std"
          layout="horizontal"
          height={420}
          colorByCategory={Object.fromEntries(chartData.map((d, i) => [
            d.name as string,
            // viridis-ish gradient
            ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"][i] ?? "#475569",
          ]))}
        />
      </Card>

      <Card title="Full leaderboard">
        <DataTable
          rows={sorted}
          cols={[
            { key: "name", label: "Model" },
            { key: "rmse", label: "Hold-out RMSE", align: "right", render: (r) => num(r.rmse, 3) },
            { key: "mae",  label: "MAE",           align: "right", render: (r) => num(r.mae, 3) },
            { key: "r2",   label: "R²",            align: "right", render: (r) => num(r.r2, 3) },
            { key: "cv_rmse_mean", label: "CV RMSE", align: "right", render: (r) => num(r.cv_rmse_mean, 3) },
            { key: "cv_rmse_std",  label: "CV std",  align: "right", render: (r) => num(r.cv_rmse_std, 3) },
          ]}
        />
      </Card>

    </div>
  );
}
