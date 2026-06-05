import { cn } from "@/lib/format";

type Props = {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  right?: React.ReactNode;
  className?: string;
  children?: React.ReactNode;
  padding?: "default" | "tight" | "none";
};

const PAD: Record<NonNullable<Props["padding"]>, string> = {
  default: "p-5",
  tight:   "p-3",
  none:    "",
};

export function Card({
  title, subtitle, right, className, children, padding = "default",
}: Props) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-zinc-200/80 bg-white",
        "shadow-[0_1px_2px_rgba(15,23,42,0.04),0_8px_24px_-12px_rgba(15,23,42,0.08)]",
        "transition-shadow hover:shadow-[0_1px_2px_rgba(15,23,42,0.05),0_12px_32px_-12px_rgba(15,23,42,0.10)]",
        className,
      )}
    >
      {(title || subtitle || right) && (
        <header className="flex items-start justify-between gap-4 border-b border-zinc-100 px-5 py-4">
          <div>
            {title && (
              <h2 className="text-base font-semibold tracking-tight text-zinc-900">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="mt-0.5 text-sm text-zinc-500 leading-relaxed">{subtitle}</p>
            )}
          </div>
          {right && <div className="shrink-0">{right}</div>}
        </header>
      )}
      <div className={PAD[padding]}>{children}</div>
    </section>
  );
}
