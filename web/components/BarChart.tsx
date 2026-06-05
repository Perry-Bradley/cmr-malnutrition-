"use client";

import {
  Bar, BarChart as RcBarChart, CartesianGrid, ResponsiveContainer,
  Tooltip, XAxis, YAxis, Cell, ErrorBar,
} from "recharts";

type Datum = Record<string, string | number>;

type Props = {
  data: Datum[];
  xKey: string;
  yKey: string;
  errorKey?: string;
  /** "horizontal" makes the bars run left -> right (categories on Y axis). */
  layout?: "horizontal" | "vertical";
  height?: number;
  unit?: string;
  /** Map of category -> color. Bars use the matched color. */
  colorByCategory?: Record<string, string>;
  fallbackColor?: string;
};

export default function BarChart({
  data, xKey, yKey, errorKey,
  layout = "vertical", height = 320, unit = "",
  colorByCategory, fallbackColor = "#dc2626",
}: Props) {
  const horizontal = layout === "horizontal";

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <RcBarChart
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 5, right: 16, left: horizontal ? 90 : 0, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          {horizontal ? (
            <>
              <XAxis type="number" tick={{ fontSize: 12 }} unit={unit} />
              <YAxis dataKey={xKey} type="category" tick={{ fontSize: 12 }} width={140} />
            </>
          ) : (
            <>
              <XAxis dataKey={xKey} tick={{ fontSize: 12 }} interval={0} angle={-30} textAnchor="end" height={70} />
              <YAxis tick={{ fontSize: 12 }} unit={unit} />
            </>
          )}
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            formatter={(v) => [
              typeof v === "number" ? `${v.toFixed(2)}${unit}` : String(v),
              yKey,
            ]}
          />
          <Bar dataKey={yKey} radius={3}>
            {data.map((d, i) => (
              <Cell
                key={i}
                fill={colorByCategory?.[d[xKey] as string] ?? fallbackColor}
              />
            ))}
            {errorKey && <ErrorBar dataKey={errorKey} width={4} stroke="#1f2937" />}
          </Bar>
        </RcBarChart>
      </ResponsiveContainer>
    </div>
  );
}
