// Client-safe constants for the choropleth map.
// (Don't put fs-based loaders in this file -- it's bundled into client components.)

/** GeoJSON property name (Cameroon admin-1) -> canonical region name used in our data. */
export const GEO_REGION_MAP: Record<string, string> = {
  "Adamaoua":   "Adamawa",
  "North-West": "Northwest",
  "South-West": "Southwest",
};

export function normaliseRegion(name: string): string {
  return GEO_REGION_MAP[name] ?? name;
}
