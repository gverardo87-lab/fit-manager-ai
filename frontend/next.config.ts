import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Permette di avviare una seconda istanza dev con cache separata:
  // NEXT_DIST_DIR=.next-dev npm run dev -- -p 3001
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
