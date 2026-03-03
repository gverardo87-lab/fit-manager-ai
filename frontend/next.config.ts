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
  // Dual-env: PORT 3001 (next dev -p 3001) → backend 8001; PORT 3000 (next start) → backend 8000.
  // process.env.PORT è impostato da Next.js in base alla flag -p (disponibile a startup time).
  rewrites: async () => {
    const port = parseInt(process.env.PORT ?? "3000");
    const backendPort = port >= 3001 ? 8001 : 8000;
    const backendBase = process.env.NEXT_PUBLIC_API_URL ?? `http://localhost:${backendPort}`;
    return [
      {
        source: "/media/:path*",
        destination: `${backendBase}/media/:path*`,
      },
    ];
  },
};

export default nextConfig;
