"use client";

import { useMemo, useState } from "react";
import type { Subregion } from "@/lib/types";
import { DataTable } from "@/components/DataTable";
import { pct, num } from "@/lib/format";

const NUMERIC_COLS: { key: keyof Subregion; label: string; fmt?: (v: number) => string }[] = [
  { key: "stunting_rate",                 label: "Stunting",     fmt: (v) => pct(v, 1) },
  { key: "wasting_pct",                   label: "Wasting",      fmt: (v) => pct(v, 1) },
  { key: "underweight_pct",               label: "Underweight",  fmt: (v) => pct(v, 1) },
  { key: "women_secondary_plus_pct",      label: "Women sec+ edu", fmt: (v) => pct(v, 0) },
  { key: "women_literate_pct",            label: "Women literate", fmt: (v) => pct(v, 0) },
  { key: "improved_water_pct",            label: "Water %",      fmt: (v) => pct(v, 0) },
  { key: "improved_sanitation_pct",       label: "Sanit %",      fmt: (v) => pct(v, 0) },
  { key: "antenatal_4plus_pct",           label: "ANC 4+",       fmt: (v) => pct(v, 0) },
  { key: "skilled_birth_attendance_pct",  label: "SBA %",        fmt: (v) => pct(v, 0) },
  { key: "health_facility_delivery_pct",  label: "Facility delivery", fmt: (v) => pct(v, 0) },
  { key: "health_insurance_any_pct",      label: "Insurance %",  fmt: (v) => pct(v, 1) },
  { key: "malaria_prevalence_pct",        label: "Malaria %",    fmt: (v) => pct(v, 0) },
  { key: "child_anemia_pct",              label: "Anaemia <5 %", fmt: (v) => pct(v, 0) },
  { key: "fertility_rate",                label: "TFR 15-49",    fmt: (v) => num(v, 2) },
];

export default function DataExplorer({ rows }: { rows: Subregion[] }) {
  const regions = useMemo(
    () => Array.from(new Set(rows.map((r) => r.region))).sort(),
    [rows]
  );
  const years = useMemo(
    () => Array.from(new Set(rows.map((r) => r.year))).sort(),
    [rows]
  );
  const breakdowns = useMemo(
    () => Array.from(new Set(rows.map((r) => r.breakdown_dim ?? "Region"))).sort(),
    [rows]
  );

  const [region, setRegion] = useState<string>("");
  const [year, setYear] = useState<number | "">("");
  const [breakdown, setBreakdown] = useState<string>("");
  const [search, setSearch] = useState("");

  const filtered = useMemo(
    () =>
      rows.filter((r) => {
        if (region && r.region !== region) return false;
        if (year && r.year !== year) return false;
        if (breakdown && (r.breakdown_dim ?? "Region") !== breakdown) return false;
        if (search) {
          const q = search.toLowerCase();
          if (!r.subregion.toLowerCase().includes(q) && !r.region.toLowerCase().includes(q)) return false;
        }
        return true;
      }),
    [rows, region, year, breakdown, search]
  );

  const csv = useMemo(() => {
    const headers = ["region", "subregion", "year", ...NUMERIC_COLS.map((c) => c.key)];
    const lines = [headers.join(",")];
    for (const r of filtered) lines.push(headers.map((h) => r[h as keyof Subregion]).join(","));
    return lines.join("\n");
  }, [filtered]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-3 items-end">
        <label className="flex flex-col gap-1 text-xs text-zinc-600">
          Region
          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="min-w-40 rounded-md border border-zinc-300 bg-white px-2.5 py-1.5 text-sm"
          >
            <option value="">All</option>
            {regions.map((r) => <option key={r}>{r}</option>)}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-zinc-600">
          Year
          <select
            value={year}
            onChange={(e) => setYear(e.target.value === "" ? "" : Number(e.target.value))}
            className="rounded-md border border-zinc-300 bg-white px-2.5 py-1.5 text-sm"
          >
            <option value="">All</option>
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-zinc-600">
          Breakdown
          <select
            value={breakdown}
            onChange={(e) => setBreakdown(e.target.value)}
            className="min-w-40 rounded-md border border-zinc-300 bg-white px-2.5 py-1.5 text-sm"
          >
            <option value="">All</option>
            {breakdowns.map((b) => <option key={b}>{b}</option>)}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-zinc-600">
          Search
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Sub-region name..."
            className="min-w-52 rounded-md border border-zinc-300 bg-white px-2.5 py-1.5 text-sm"
          />
        </label>

        <div className="ml-auto flex items-center gap-3">
          <span className="text-sm text-zinc-600">
            {filtered.length.toLocaleString()} rows
          </span>
          <a
            href={`data:text/csv;charset=utf-8,${encodeURIComponent(csv)}`}
            download="cameroon_subregional_filtered.csv"
            className="inline-flex items-center rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-zinc-800"
          >
            Download CSV
          </a>
        </div>
      </div>

      <DataTable
        rows={filtered}
        cols={[
          { key: "breakdown_dim", label: "Breakdown", className: "text-zinc-500",
            render: (r) => r.breakdown_dim ?? "Region" },
          { key: "subregion", label: "Sub-population" },
          { key: "region", label: "Region", className: "text-zinc-500" },
          { key: "year", label: "Year", align: "right" },
          ...NUMERIC_COLS.map((c) => ({
            key: c.key, label: c.label, align: "right" as const,
            render: (r: Subregion) => (c.fmt ? c.fmt(r[c.key] as number) : String(r[c.key])),
          })),
        ]}
      />
    </div>
  );
}
