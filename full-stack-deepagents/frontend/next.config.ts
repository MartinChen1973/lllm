import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* start-all.bat opens http://127.0.0.1:3500 — allow dev HMR from that host */
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
