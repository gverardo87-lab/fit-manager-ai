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
 * Mapping:
 *   http://192.168.1.23:3000  → http://192.168.1.23:8000/api   (LAN casa)
 *   http://100.64.0.1:3000    → http://100.64.0.1:8000/api     (Tailscale)
 *   http://localhost:3001     → http://localhost:8001/api       (dev)
 *
 * Fallback SSR: NEXT_PUBLIC_API_URL (per eventuale server-side rendering).
 */
function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const { hostname, port } = window.location;
    const apiPort = port === "3001" ? "8001" : "8000";
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
// RESPONSE INTERCEPTOR — Redirect su 401
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
