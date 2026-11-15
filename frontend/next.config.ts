import type { NextConfig } from "next";

// Static export: `next build` writes plain HTML/JS to out/, which Caddy serves
// directly on the VM (no Node.js there). All data is fetched client-side from
// the FastAPI backend, so nothing here needs a server.
const nextConfig: NextConfig = {
  output: "export",
  // Emit /admin/index.html (not /admin.html beside an /admin/ prefetch folder) so
  // Caddy's plain directory lookup serves every page - see deploy/remove_memos.sh.
  trailingSlash: true,
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
