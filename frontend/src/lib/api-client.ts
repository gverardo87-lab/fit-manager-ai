// src/lib/api-client.ts
/**
 * Client API centralizzato — istanza Axios configurata.
 *
 * Architettura:
 * - Base URL DINAMICO: derivato da window.location (hostname + porta)
 *   → Funziona automaticamente da qualsiasi rete (LAN, Tailscale, localhost)
 *   → Regola: porta frontend 3000 → backend 8000, porta 3001 → backend 8001
 *   → Fallback SSR: env var NEXT_PUBLIC_API_URL
 * - Request interceptor: allega JWT token da cookie ad ogni richiesta
 * - Response interceptor: redirect a /login su 401 Unauthorized
 * - Timeout: 15 secondi (ragionevole per API locale)
 *
 * Il token JWT viene letto dai cookie (tramite js-cookie),
 * NON da localStorage. I cookie sono piu' sicuri perche':
 * - Non accessibili da XSS (se HttpOnly, ma qui usiamo JS cookie per semplicita')
 * - Persistono tra le tab del browser
 * - Possono avere scadenza controllata
 */

import axios from "axios";
import Cookies from "js-cookie";

// Nome del cookie dove salviamo il JWT
export const TOKEN_COOKIE = "fitmanager_token";

// ════════════════════════════════════════════════════════════
// DYNAMIC API URL — dedotto dal browser, zero config
// ════════════════════════════════════════════════════════════

/**
 * Deriva l'URL del backend dall'hostname e porta del frontend.
 *
 * 3 modalita':
 *   https://giacomo.tail8a3bc3.ts.net  → /api  (Tailscale Funnel — proxy Next.js)
 *   http://192.168.1.23:3000           → http://192.168.1.23:8000/api  (LAN)
 *   http://localhost:3001              → http://localhost:8001/api      (dev)
 *
 * Logica: se HTTPS o nessuna porta esplicita → siamo dietro un reverse proxy
 * (Funnel/nginx). Le chiamate passano come URL relativi, Next.js proxya al backend.
 * Altrimenti: mapping diretto porta frontend → porta backend.
 *
 * Fallback SSR: NEXT_PUBLIC_API_URL (per eventuale server-side rendering).
 */
function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const { protocol, hostname, port } = window.location;

    // Tailscale Funnel / reverse proxy: HTTPS o nessuna porta esplicita
    // → URL relativo, Next.js rewrite proxya al backend localhost
    if (protocol === "https:" || !port) {
      return "/api";
    }

    // Accesso diretto con porta esplicita (LAN, localhost, Tailscale VPN)
    // Mapping generico: 3000→8000, 3001→8001, 3002→8002, ecc.
    const frontPort = parseInt(port) || 3000;
    const apiPort = frontPort - 3000 + 8000;
    return `http://${hostname}:${apiPort}/api`;
  }
  return `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api`;
}

// Istanza Axios configurata
const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ════════════════════════════════════════════════════════════
// REQUEST INTERCEPTOR — Allega JWT ad ogni richiesta
// ════════════════════════════════════════════════════════════

apiClient.interceptors.request.use(
  (config) => {
    const token = Cookies.get(TOKEN_COOKIE);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ════════════════════════════════════════════════════════════
// RESPONSE INTERCEPTOR — Redirect su 401 / 403 license
// ════════════════════════════════════════════════════════════

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token scaduto o invalido — rimuovi cookie
      Cookies.remove(TOKEN_COOKIE);

      // Redirect al login, MA solo se non siamo gia' sulla pagina login.
      // Senza questo check, un 401 dal login endpoint (credenziali errate)
      // causerebbe un reload silenzioso della pagina, perdendo il messaggio
      // di errore che il componente vuole mostrare.
      if (
        typeof window !== "undefined" &&
        !window.location.pathname.startsWith("/login")
      ) {
        window.location.href = "/login";
      }
    }

    // Licenza non valida/scaduta — redirect a /licenza
    if (error.response?.status === 403) {
      const licenseStatus = error.response?.data?.license_status;
      if (
        licenseStatus &&
        typeof window !== "undefined" &&
        !window.location.pathname.startsWith("/licenza")
      ) {
        window.location.href = `/licenza?status=${licenseStatus}`;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;

// ════════════════════════════════════════════════════════════
// ERROR EXTRACTION — Estrae detail dal backend FastAPI
// ════════════════════════════════════════════════════════════

/** Estrae `error.response.data.detail` da errori Axios, con fallback generico. */
export function extractErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}
