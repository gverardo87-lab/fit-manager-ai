// src/lib/api-client.ts
/**
 * Client API centralizzato — istanza Axios configurata.
 *
 * Architettura:
 * - Base URL da variabile d'ambiente NEXT_PUBLIC_API_URL
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

// Istanza Axios configurata
const apiClient = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_API_URL}/api`,
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
