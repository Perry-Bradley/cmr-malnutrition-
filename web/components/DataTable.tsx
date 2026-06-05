import { cn } from "@/lib/format";

type Col<T> = {
  key: keyof T | string;
  label: string;
  className?: string;
  align?: "left" | "right" | "center";
  render?: (row: T) => React.ReactNode;
};

type Props<T> = {
  rows: T[];
  cols: Col<T>[];
  className?: string;
  zebra?: boolean;
};

export function DataTable<T extends Record<string, unknown>>({
  rows, cols, className, zebra = true,
}: Props<T>) {
  return (
    <div className={cn(
      "overflow-x-auto rounded-xl border border-zinc-200 bg-white",
      className,
    )}>
      <table className="min-w-full divide-y divide-zinc-200 text-sm">
        <thead className="bg-zinc-50/80 sticky top-0 backdrop-blur">
          <tr>
            {cols.map((c) => (
              <th
                key={String(c.key)}
                scope="col"
                className={cn(
                  "px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-zinc-500",
                  c.align === "right" ? "text-right" : c.align === "center" ? "text-center" : "text-left",
                  c.className,
                )}
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 bg-white">
          {rows.map((row, i) => (
            <tr
              key={i}
              className={cn(
                zebra && i % 2 === 1 && "bg-zinc-50/40",
                "transition-colors hover:bg-amber-50/40",
              )}
            >
              {cols.map((c) => {
                const v = c.render ? c.render(row) : (row[c.key as keyof T] as React.ReactNode);
                return (
                  <td
                    key={String(c.key)}
                    className={cn(
                      "whitespace-nowrap px-3 py-2.5 text-zinc-700 tabular-nums",
                      c.align === "right" ? "text-right" : c.align === "center" ? "text-center" : "text-left",
                      c.className,
                    )}
                  >
                    {v as React.ReactNode}
                  </td>
                );
              })}
            </tr>
          ))}
          {!rows.length && (
            <tr>
              <td colSpan={cols.length} className="px-3 py-12 text-center text-sm text-zinc-400">
                No rows match the current filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
