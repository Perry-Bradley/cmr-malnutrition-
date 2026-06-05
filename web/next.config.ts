import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    // Silence the "multiple lockfiles" warning by pinning the root to this app.
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
