import type { NextConfig } from "next";

// Static export: `next build` writes plain HTML/JS to out/, which Caddy serves
// directly on the VM (no Node.js there). All data is fetched client-side from
// the FastAPI backend, so nothing here needs a server.
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
