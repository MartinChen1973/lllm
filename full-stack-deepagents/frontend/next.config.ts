import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  /* start-all.bat opens http://127.0.0.1:3500 — allow dev HMR from that host */
  allowedDevOrigins: ["127.0.0.1"],
  /* ⬇️ Monorepo: parent `lllm/package-lock.json` otherwise wins and triggers Turbopack root warning */
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
