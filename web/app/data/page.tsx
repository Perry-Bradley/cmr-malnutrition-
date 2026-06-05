import DataExplorer from "./DataExplorer";
import { Card } from "@/components/Card";
import { getSubregional } from "@/lib/data";

export const metadata = { title: "Data — Cameroon Malnutrition Atlas" };

export default async function DataPage() {
  const rows = await getSubregional();
  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Data explorer</h1>
        <p className="mt-1 text-zinc-600">
          The full analysis table: one row per Cameroonian sub-region per survey year.
          Filter by region or year, search by sub-region, and download the filtered
          subset as CSV.
        </p>
      </header>
      <Card>
        <DataExplorer rows={rows} />
      </Card>
    </div>
  );
}
