import { cn } from "@/lib/format";

type Props = {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  tone?: "default" | "danger" | "good" | "warning";
  icon?: React.ReactNode;
  className?: string;
};

const TONE: Record<NonNullable<Props["tone"]>, {
  ring: string; value: string; accent: string; bg: string;
}> = {
  default: { ring: "ring-zinc-200",    value: "text-zinc-900",    accent: "bg-zinc-100 text-zinc-600",        bg: "bg-white" },
  danger:  { ring: "ring-red-200/80",  value: "text-red-700",     accent: "bg-red-100 text-red-700",          bg: "bg-gradient-to-br from-red-50/80 to-white" },
  good:    { ring: "ring-emerald-200", value: "text-emerald-800", accent: "bg-emerald-100 text-emerald-700",  bg: "bg-gradient-to-br from-emerald-50/80 to-white" },
  warning: { ring: "ring-amber-200",   value: "text-amber-800",   accent: "bg-amber-100 text-amber-700",      bg: "bg-gradient-to-br from-amber-50/80 to-white" },
};

export function KpiTile({
  label, value, hint, tone = "default", icon, className,
}: Props) {
  const t = TONE[tone];
  return (
    <div
      className={cn(
        "group relative rounded-2xl px-5 py-4 ring-1",
        "shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition-all hover:shadow-[0_8px_24px_-12px_rgba(15,23,42,0.12)]",
        t.bg, t.ring, className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.06em] text-zinc-500">
          {label}
        </div>
        {icon && (
          <span className={cn("rounded-lg p-1.5", t.accent)}>{icon}</span>
        )}
      </div>
      <div className={cn("mt-2 text-3xl font-semibold tabular-nums tracking-tight",
                          t.value)}>
        {value}
      </div>
      {hint && (
        <div className="mt-1.5 text-xs text-zinc-500 leading-relaxed">
          {hint}
        </div>
      )}
    </div>
  );
}
