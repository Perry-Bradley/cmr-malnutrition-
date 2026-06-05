"use client";

import { useEffect, useMemo, useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { geoMercator } from "d3-geo";
import { scaleSequential } from "d3-scale";
import { normaliseRegion } from "@/lib/geo";
import { pct } from "@/lib/format";

type Props = {
  values: Record<string, number>;
  unitLabel?: string;
  domain?: [number, number];
  height?: number;
};

const GEO_URL = "/data/cameroon_admin1.geojson";

// Internal SVG viewBox. The SVG scales to the container via CSS, so we can
// reason about projection scale + center against ONE fixed coordinate system
// instead of fighting the live container size.
const VB_W = 800;
const VB_H = 720;

const stops: [number, string][] = [
  [0,    "#15803d"],
  [0.25, "#a3e635"],
  [0.5,  "#facc15"],
  [0.75, "#f97316"],
  [1,    "#7f1d1d"],
];

function interp(t: number) {
  t = Math.max(0, Math.min(1, t));
  let i = 0;
  while (i < stops.length - 1 && t > stops[i + 1][0]) i++;
  const [t0, c0] = stops[i];
  const [t1, c1] = stops[Math.min(i + 1, stops.length - 1)];
  const f = (t - t0) / Math.max(1e-9, t1 - t0);
  const hex = (h: string) => [1, 3, 5].map((j) => parseInt(h.slice(j, j + 2), 16));
  const [r0, g0, b0] = hex(c0);
  const [r1, g1, b1] = hex(c1);
  const mix = (a: number, b: number) => Math.round(a + (b - a) * f);
  return `rgb(${mix(r0, r1)},${mix(g0, g1)},${mix(b0, b1)})`;
}

// Cameroon's actual bounding box (from the geoBoundaries ADM1 file):
//   lng 8.50 - 16.19  (7.69° wide)
//   lat 1.66 - 13.08  (11.42° tall)
// Height is the limiting dimension for a Mercator projection on this viewBox.
// Empirical math: to fit 11.42° of latitude into 688 pixels of viewBox height,
// scale = 688 / (mercatorY(13.08) - mercatorY(1.66)) ≈ 3400.
// Centred on lng 12.0, visual-centre lat 7.7° (Mercator midpoint, not geom).
const PROJECTION = geoMercator()
  .center([12.0, 7.7])
  .scale(3400)
  .translate([VB_W / 2, VB_H / 2]);

export default function ChoroplethMap({
  values, unitLabel = "%", domain, height = 480,
}: Props) {
  const [hover, setHover] = useState<{ region: string; value?: number; x: number; y: number } | null>(null);
  const [geoLoaded, setGeoLoaded] = useState(false);

  // Once the GeoJSON has loaded, refit the projection to its actual bounding
  // box so it's pixel-perfect regardless of dataset updates upstream.
  useEffect(() => {
    let cancelled = false;
    fetch(GEO_URL)
      .then((r) => r.json())
      .then((j) => {
        if (cancelled) return;
        try {
          PROJECTION.fitExtent([[16, 16], [VB_W - 16, VB_H - 16]], j);
        } catch { /* keep manual scale fallback */ }
        setGeoLoaded(true);
      })
      .catch(() => { /* keep manual scale fallback */ });
    return () => { cancelled = true; };
  }, []);

  const [vmin, vmax] = useMemo<[number, number]>(() => {
    if (domain) return domain;
    const vals = Object.values(values);
    if (!vals.length) return [0, 1];
    return [Math.min(...vals), Math.max(...vals)];
  }, [values, domain]);
  const scale = scaleSequential((t) => interp(t)).domain([vmin, vmax]);

  return (
    <div className="relative w-full" style={{ height }}>
      <ComposableMap
        projection={PROJECTION}
        width={VB_W}
        height={VB_H}
        style={{ width: "100%", height: "100%" }}
      >
        <Geographies geography={GEO_URL}>
          {({ geographies }) =>
            geographies.map((g) => {
              const rawName = g.properties.shapeName ?? g.properties.name;
              const region = normaliseRegion(rawName);
              const v = values[region];
              const isHovered = hover?.region === region;
              const fill = v == null ? "#e5e7eb" : (scale(v) as string);
              return (
                <Geography
                  key={`${g.rsmKey}-${geoLoaded ? "ready" : "pending"}`}
                  geography={g}
                  fill={fill}
                  stroke={isHovered ? "#18181b" : "#ffffff"}
                  strokeWidth={isHovered ? 1.6 : 0.8}
                  style={{
                    default: { outline: "none", transition: "filter 0.15s, stroke-width 0.15s, stroke 0.15s" },
                    hover:   { outline: "none", filter: "brightness(1.1) drop-shadow(0 2px 6px rgba(0,0,0,0.18))", cursor: "pointer" },
                    pressed: { outline: "none" },
                  }}
                  onMouseEnter={(e) => setHover({ region, value: v, x: e.clientX, y: e.clientY })}
                  onMouseMove={(e)  => setHover((h) => h && { ...h, x: e.clientX, y: e.clientY })}
                  onMouseLeave={() => setHover(null)}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 rounded-xl bg-white/95 px-3 py-2 text-xs shadow-lg ring-1 ring-zinc-200 backdrop-blur">
        <div className="mb-1 font-medium text-zinc-700">
          {unitLabel === "%" ? "Predicted stunting" : unitLabel}
        </div>
        <div className="flex items-center gap-2">
          <span className="tabular-nums text-zinc-600">{vmin.toFixed(0)}{unitLabel}</span>
          <div
            className="h-2 w-32 rounded-full ring-1 ring-zinc-200"
            style={{
              background:
                "linear-gradient(to right, #15803d, #a3e635, #facc15, #f97316, #7f1d1d)",
            }}
          />
          <span className="tabular-nums text-zinc-600">{vmax.toFixed(0)}{unitLabel}</span>
        </div>
      </div>

      {/* Tooltip */}
      {hover && (
        <div
          className="pointer-events-none fixed z-50 rounded-lg bg-zinc-900/95 px-3 py-2 text-xs text-white shadow-2xl ring-1 ring-black/20 backdrop-blur"
          style={{ top: hover.y + 14, left: hover.x + 14 }}
        >
          <div className="font-semibold tracking-tight">{hover.region}</div>
          <div className="mt-0.5 text-zinc-300">
            {hover.value == null
              ? <span className="text-zinc-400">no data</span>
              : <><span className="text-base font-medium text-white tabular-nums">{pct(hover.value, 1)}</span> stunting</>}
          </div>
        </div>
      )}
    </div>
  );
}
