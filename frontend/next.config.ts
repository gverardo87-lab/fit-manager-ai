import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output: produce .next/standalone/ con server.js autonomo.
  // Per distribuzione (installer) non serve Node.js di sistema — solo node.exe bundled.
  output: "standalone",

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
  // Mapping generico: porta frontend - 3000 + 8000 = porta backend.
  // 3000→8000 (prod), 3001→8001 (dev), 3002→8002 (installer test).
  rewrites: async () => {
    const port = parseInt(process.env.PORT ?? "3000");
    const backendPort = port - 3000 + 8000;
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
