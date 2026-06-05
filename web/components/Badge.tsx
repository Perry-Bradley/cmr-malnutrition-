import { BAND_COLOR, cn } from "@/lib/format";

export function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        "bg-zinc-100 text-zinc-700 ring-zinc-200",
        className,
      )}
    >
      {children}
    </span>
  );
}

const BAND_DOT: Record<string, string> = {
  low:      "bg-emerald-500",
  medium:   "bg-amber-500",
  high:     "bg-orange-500",
  critical: "bg-red-600",
};

export function RiskBandBadge({ band }: { band?: string }) {
  const key = (band ?? "").toLowerCase();
  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
      BAND_COLOR[key] ?? "bg-zinc-100 text-zinc-700 ring-zinc-200",
    )}>
      <span className={cn("inline-block h-1.5 w-1.5 rounded-full", BAND_DOT[key] ?? "bg-zinc-400")} />
      {band ?? "—"}
    </span>
  );
}
