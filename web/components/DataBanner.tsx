import { Info } from "lucide-react";

export function DataBanner() {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-blue-200/70 bg-gradient-to-br from-blue-50/80 to-sky-50/40 px-4 py-3.5 text-sm text-blue-900 shadow-sm">
      <div className="mt-0.5 shrink-0 rounded-md bg-blue-100/80 p-1">
        <Info className="h-4 w-4" />
      </div>
      <div className="leading-relaxed">
        <span className="font-semibold">Real Cameroon DHS data only.</span>{" "}
        <span className="text-blue-900/85">
          220 sub-population observations pulled live from the public DHS Program API
          (5 DHS rounds · 1991–2018 · 11 breakdown dimensions including region,
          wealth quintile, mother&apos;s education, residence, child sex, age in months).
          1991/1998 mega-regions are broadcast to constituent modern regions.
          Hypothesis tests run on the geographic slice only.
        </span>
      </div>
    </div>
  );
}
