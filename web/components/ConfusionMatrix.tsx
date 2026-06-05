import { cn } from "@/lib/format";

type Props = {
  matrix: number[][];
  labels: string[];
};

export function ConfusionMatrix({ matrix, labels }: Props) {
  const flat = matrix.flat();
  const vmax = Math.max(1, ...flat);

  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-1 text-xs">
        <thead>
          <tr>
            <th />
            <th className="px-2 py-1 text-zinc-500 font-normal" colSpan={labels.length}>
              Predicted
            </th>
          </tr>
          <tr>
            <th className="text-zinc-500 font-normal pr-2">Actual ↓</th>
            {labels.map((l) => (
              <th key={l} className="px-2 py-1 text-zinc-600 font-medium">{l}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <th className="pr-2 text-right text-zinc-700 font-medium">{labels[i]}</th>
              {row.map((v, j) => {
                const t = v / vmax;
                const isDiag = i === j;
                return (
                  <td
                    key={j}
                    className={cn(
                      "h-10 w-12 rounded-md text-center tabular-nums",
                      isDiag ? "text-emerald-900 ring-1 ring-emerald-300" : "text-zinc-800 ring-1 ring-zinc-200",
                    )}
                    style={{
                      backgroundColor: isDiag
                        ? `rgba(16,185,129,${0.15 + 0.6 * t})`
                        : `rgba(244,63,94,${0.05 + 0.45 * t})`,
                    }}
                  >
                    {v}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
