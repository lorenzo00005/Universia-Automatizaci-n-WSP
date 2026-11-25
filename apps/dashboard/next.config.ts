import type { NextConfig } from "next";

// En Docker, Caddy manda /api/* a la API y el resto al dashboard.
// Con `pnpm dev` sin Caddy, Next reenvía /api/* a la API local.
const apiUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    return [{ source: "/api/:path*", destination: `${apiUrl}/:path*` }];
  },
};

export default nextConfig;
