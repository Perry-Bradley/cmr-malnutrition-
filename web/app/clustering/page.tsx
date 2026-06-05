import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { KpiTile } from "@/components/KpiTile";
import type { ClusterProfile } from "@/lib/types";
import {
  getClusterAssignments, getClusterProfiles, getElbow,
} from "@/lib/data";
import { num, pct } from "@/lib/format";

function ProfileRow({ p, field, label, fmt }:
  { p: ClusterProfile; field: string; label: string; fmt: "pct" | "num" }) {
  const v = (p as unknown as Record<string, number>)[field];
  if (typeof v !== "number") return null;
  const text = fmt === "pct" ? pct(v, 0) : num(v, 2);
  return (
    <>
      <li className="text-zinc-600">{label}</li>
      <li className="text-right tabular-nums">{text}</li>
    </>
  );
}

export const metadata = { title: "Clustering — Cameroon Malnutrition Atlas" };

export default async function ClusteringPage() {
  const [profiles, assignments, elbow] = await Promise.all([
    getClusterProfiles(), getClusterAssignments(), getElbow(),
  ]);

  const bestK = elbow.length
    ? elbow.reduce((a, b) => (a.silhouette > b.silhouette ? a : b))
    : null;

  // sorted profiles by stunting rate
  const sortedProfiles = [...profiles].sort((a, b) => b.stunting_rate - a.stunting_rate);

  return (
    <div className="flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Clustering</h1>
        <p className="mt-1 text-zinc-600">
          Unsupervised grouping of sub-regions by their <em>drivers</em> (education, WASH,
          wealth, healthcare access, disease burden) — irrespective of their current
          stunting outcome. Useful for tailoring intervention packages: each cluster
          shares a recognisable profile and likely needs a similar response.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Best k (silhouette)"  value={bestK?.k ?? "—"}                              tone="good" />
        <KpiTile label="Silhouette score"     value={bestK ? num(bestK.silhouette, 3) : "—"}        hint="higher = tighter clusters" tone="good" />
        <KpiTile label="Clusters built"       value={profiles.length}                              />
        <KpiTile label="Sub-regions clustered" value={assignments.length}                          />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {sortedProfiles.map((p) => (
          <Card
            key={p.cluster}
            title={p.cluster_label}
            subtitle={`${p.n_subregions} regions · mean stunting ${pct(p.stunting_rate as number, 1)}`}
          >
            <ul className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
              <ProfileRow p={p} field="women_secondary_plus_pct"     label="Women sec+ education" fmt="pct" />
              <ProfileRow p={p} field="women_literate_pct"           label="Women literate"        fmt="pct" />
              <ProfileRow p={p} field="improved_water_pct"           label="Improved water"        fmt="pct" />
              <ProfileRow p={p} field="improved_sanitation_pct"      label="Improved sanitation"   fmt="pct" />
              <ProfileRow p={p} field="antenatal_4plus_pct"          label="ANC 4+ visits"         fmt="pct" />
              <ProfileRow p={p} field="skilled_birth_attendance_pct" label="Skilled birth att."    fmt="pct" />
              <ProfileRow p={p} field="health_facility_delivery_pct" label="Facility delivery"     fmt="pct" />
              <ProfileRow p={p} field="health_insurance_any_pct"     label="Any insurance"         fmt="pct" />
              <ProfileRow p={p} field="malaria_prevalence_pct"       label="Malaria (RDT)"         fmt="pct" />
              <ProfileRow p={p} field="child_anemia_pct"             label="Under-5 anaemia"       fmt="pct" />
              <ProfileRow p={p} field="wasting_pct"                  label="Under-5 wasting"       fmt="pct" />
              <ProfileRow p={p} field="underweight_pct"              label="Under-5 underweight"   fmt="pct" />
              <ProfileRow p={p} field="fertility_rate"               label="Fertility rate"        fmt="num" />
            </ul>
          </Card>
        ))}
      </div>

      <Card title="Elbow + silhouette scan" subtitle="Within-cluster inertia and mean silhouette for k = 2..8">
        <DataTable
          rows={elbow}
          cols={[
            { key: "k",          label: "k", align: "right" },
            { key: "inertia",    label: "Inertia",    align: "right", render: (r) => num(r.inertia, 2) },
            { key: "silhouette", label: "Silhouette", align: "right", render: (r) => num(r.silhouette, 3) },
          ]}
        />
      </Card>

      <Card title="Cluster assignment per sub-region">
        <DataTable
          rows={assignments}
          cols={[
            { key: "subregion",      label: "Sub-region" },
            { key: "region",         label: "Region",         className: "text-zinc-500" },
            { key: "cluster_label",  label: "Cluster" },
            { key: "stunting_rate",  label: "Observed stunting", align: "right", render: (r) => pct(r.stunting_rate as number, 1) },
          ]}
        />
      </Card>
    </div>
  );
}
