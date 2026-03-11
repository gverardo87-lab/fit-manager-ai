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
  // IMPORTANTE: questi rewrite vengono serializzati nel server standalone buildato.
  // Non devono mai dipendere da URL browser-facing o variabili ambiente lato client,
  // altrimenti il bundle installer puo' congelare un host di sviluppo (LAN/Tailscale)
  // e proxyare /api verso la macchina sbagliata sul PC del cliente.
  rewrites: async () => {
    const port = parseInt(process.env.PORT ?? "3000");
    const backendPort = port - 3000 + 8000;
    const backendBase = `http://127.0.0.1:${backendPort}`;
    return [
      {
        source: "/health",
        destination: `${backendBase}/health`,
      },
      {
        source: "/media/:path*",
        destination: `${backendBase}/media/:path*`,
      },
      // Proxy TUTTE le chiamate /api/* al backend FastAPI.
      // Indispensabile per Tailscale Funnel: il browser chiama URL relativi
      // same-origin, Next.js proxya server-side a localhost.
      // Zero CORS, zero mixed content (HTTPS frontend → HTTP backend localhost).
      {
        source: "/api/:path*",
        destination: `${backendBase}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
