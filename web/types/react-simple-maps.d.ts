// Minimal type stubs for react-simple-maps so the project builds under strict TS.
// The library ships its own types only via @types/react-simple-maps, which doesn't
// pin react 19; rather than fight peer deps we declare just what we use.

declare module "react-simple-maps" {
  import type { CSSProperties, ReactNode, MouseEvent } from "react";
  import type { GeoProjection } from "d3-geo";

  export interface ComposableMapProps {
    /** Projection name (e.g. "geoMercator") OR a pre-built d3 projection. */
    projection?: string | GeoProjection;
    projectionConfig?: Record<string, unknown>;
    width?: number;
    height?: number;
    style?: CSSProperties;
    children?: ReactNode;
  }
  export const ComposableMap: (props: ComposableMapProps) => JSX.Element;

  export interface GeoFeature {
    rsmKey: string;
    properties: Record<string, string>;
  }

  export interface GeographiesProps {
    geography: string | object;
    children: (args: { geographies: GeoFeature[] }) => ReactNode;
  }
  export const Geographies: (props: GeographiesProps) => JSX.Element;

  export interface GeographyStyle {
    default?: CSSProperties;
    hover?: CSSProperties;
    pressed?: CSSProperties;
  }
  export interface GeographyProps {
    geography: GeoFeature;
    fill?: string;
    stroke?: string;
    strokeWidth?: number;
    style?: GeographyStyle;
    onMouseEnter?: (e: MouseEvent<SVGPathElement>) => void;
    onMouseMove?: (e: MouseEvent<SVGPathElement>) => void;
    onMouseLeave?: (e: MouseEvent<SVGPathElement>) => void;
  }
  export const Geography: (props: GeographyProps) => JSX.Element;
}
