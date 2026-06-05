export const pct  = (v: number, d = 1) => `${v.toFixed(d)}%`;
export const num  = (v: number, d = 2) => v.toFixed(d);
export const pval = (v: number) =>
  v < 1e-6 ? "p < 1e-6" : v < 0.001 ? `p < 0.001` : `p = ${v.toFixed(3)}`;

export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

// Risk band -> tailwind classes
export const BAND_COLOR: Record<string, string> = {
  low:      "bg-emerald-100 text-emerald-700 ring-emerald-200",
  medium:   "bg-amber-100   text-amber-700   ring-amber-200",
  high:     "bg-orange-100  text-orange-700  ring-orange-200",
  critical: "bg-red-100     text-red-700     ring-red-200",
};

// Region -> consistent color (reused for charts + legends)
export const REGION_COLOR: Record<string, string> = {
  "Far North":  "#7f1d1d",
  "North":      "#b91c1c",
  "Adamawa":    "#dc2626",
  "East":       "#ea580c",
  "Northwest":  "#d97706",
  "Southwest":  "#65a30d",
  "West":       "#16a34a",
  "South":      "#0891b2",
  "Centre":     "#2563eb",
  "Littoral":   "#7c3aed",
};
