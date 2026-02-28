import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Permette di avviare una seconda istanza dev con cache separata:
  // NEXT_DIST_DIR=.next-dev npm run dev -- -p 3001
  distDir: process.env.NEXT_DIST_DIR || ".next",

  // Permette a <Image> di caricare media dall'API backend (StaticFiles)
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "localhost" },
      { protocol: "http", hostname: "127.0.0.1" },
    ],
  },

  // Proxy /media/* al backend — rende i fetch same-origin (evita CORS su StaticFiles).
  // Necessario per l'export Excel che usa fetch() per scaricare immagini esercizi.
  rewrites: async () => [
    {
      source: "/media/:path*",
      destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/media/:path*`,
    },
  ],
};

export default nextConfig;
